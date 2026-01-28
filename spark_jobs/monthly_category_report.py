import os
import sys
from datetime import datetime, timezone
import psycopg2
from pyspark.sql import SparkSession, functions as F


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[spark_job] {ts} | {msg}", flush=True)


PG_HOST = os.environ.get("POSTGRES_HOST", "db")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ.get("POSTGRES_DB", "montra_db")
PG_USER = os.environ.get("POSTGRES_USER", "montra_user")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "montra_pass")

# Optional: run only for a given period
REPORT_YEAR = os.environ.get("REPORT_YEAR")    # e.g. "2026"
REPORT_MONTH = os.environ.get("REPORT_MONTH")  # e.g. "1" or "01"

# Tuning knobs
NUM_PARTITIONS = int(os.environ.get("SPARK_JDBC_PARTITIONS", "8"))
FETCH_SIZE = os.environ.get("SPARK_JDBC_FETCHSIZE", "10000")

JDBC_URL = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"

TX_TABLE = "transactions_transaction"
OUT_TABLE = "transactions_monthlycategoryreport"


def _pg_connect():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    )


def truncate_output_table() -> None:
    conn = _pg_connect()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {OUT_TABLE} RESTART IDENTITY;")
    finally:
        conn.close()


def delete_period_from_output_table(year: int, month: int) -> None:
    conn = _pg_connect()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {OUT_TABLE} WHERE year = %s AND month = %s;",
                (year, month),
            )
    finally:
        conn.close()


def parse_period():
    if REPORT_YEAR and REPORT_MONTH:
        y = int(REPORT_YEAR)
        m = int(REPORT_MONTH)
        if m < 1 or m > 12:
            raise ValueError("REPORT_MONTH must be 1..12")
        return y, m
    return None


spark = (
    SparkSession.builder
    .appName("monthly_category_report")
    .getOrCreate()
)

spark.conf.set("spark.sql.shuffle.partitions", str(max(NUM_PARTITIONS, 8)))

period = parse_period()

# Build SQL WHERE (pushdown filter to Postgres)
where_clauses = ["kind = 'expense'"]

if period:
    y, m = period
    log(f"Mode: MONTHLY_REFRESH year={y} month={m:02d}")
    log(f"Deleting existing rows for {y}-{m:02d} from {OUT_TABLE}")
    delete_period_from_output_table(y, m)

    # Postgres date filters (sargable)
    where_clauses.append(f"EXTRACT(YEAR FROM date) = {y}")
    where_clauses.append(f"EXTRACT(MONTH FROM date) = {m}")

else:
    log("Mode: FULL_REFRESH (all months)")
    log(f"Truncating output table {OUT_TABLE}")
    truncate_output_table()

where_sql = " AND ".join(where_clauses)

TX_SRC = (
    f"(SELECT id, user_id, category_id, amount, date "
    f" FROM {TX_TABLE} "
    f" WHERE {where_sql}) AS tx"
)

log(f"Reading source: {TX_SRC}")
log(f"JDBC fetchsize={FETCH_SIZE}, partitions={NUM_PARTITIONS}")

base_reader = (
    spark.read.format("jdbc")
    .option("url", JDBC_URL)
    .option("dbtable", TX_SRC)
    .option("user", PG_USER)
    .option("password", PG_PASS)
    .option("driver", "org.postgresql.Driver")
    .option("fetchsize", str(FETCH_SIZE))
)

# Partition bounds for the filtered dataset
bounds_src = f"(SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM {TX_TABLE} WHERE {where_sql}) AS b"

bounds = (
    spark.read.format("jdbc")
    .option("url", JDBC_URL)
    .option("dbtable", bounds_src)
    .option("user", PG_USER)
    .option("password", PG_PASS)
    .option("driver", "org.postgresql.Driver")
    .load()
    .collect()[0]
)

min_id = bounds["min_id"]
max_id = bounds["max_id"]

if min_id is None or max_id is None:
    log("No matching transactions found (nothing to aggregate). Exiting OK.")
    spark.stop()
    sys.exit(0)

log(f"Partition bounds: id {min_id}..{max_id}")

df = (
    base_reader
    .option("partitionColumn", "id")
    .option("lowerBound", str(min_id))
    .option("upperBound", str(max_id))
    .option("numPartitions", str(NUM_PARTITIONS))
    .load()
)

df = (
    df.withColumn("year", F.year(F.col("date")))
      .withColumn("month", F.month(F.col("date")))
)

agg = (
    df.groupBy("user_id", "category_id", "year", "month")
    .agg(
        F.sum(F.col("amount")).alias("total_amount"),
        F.avg(F.col("amount")).alias("avg_amount"),
        F.count(F.lit(1)).alias("tx_count"),
    )
    .withColumn("computed_at", F.current_timestamp())
)

log(f"Writing aggregates to {OUT_TABLE} with mode=append")

(
    agg.write.format("jdbc")
    .option("url", JDBC_URL)
    .option("dbtable", OUT_TABLE)
    .option("user", PG_USER)
    .option("password", PG_PASS)
    .option("driver", "org.postgresql.Driver")
    .mode("append")
    .save()
)

log("Done.")
spark.stop()
