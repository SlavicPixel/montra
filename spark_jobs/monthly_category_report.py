import os
import sys
from datetime import datetime, timezone
from pyspark.sql import SparkSession, functions as F
import psycopg2

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[spark_job] {ts} | {msg}", flush=True)

def truncate_output_table():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {OUT_TABLE} RESTART IDENTITY;")
    conn.close()

def delete_period_from_output_table(year: int, month: int):
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {OUT_TABLE} WHERE year = %s AND month = %s;",
            (year, month),
        )
    conn.close()

PG_HOST = os.environ.get("POSTGRES_HOST", "db")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ.get("POSTGRES_DB", "montra_db")
PG_USER = os.environ.get("POSTGRES_USER", "montra_user")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "montra_pass")

# Optional: run only for a given period (nice for "periodic processing")
REPORT_YEAR = os.environ.get("REPORT_YEAR")   # e.g. "2026"
REPORT_MONTH = os.environ.get("REPORT_MONTH") # e.g. "1" or "01"

# Tuning knobs (safe defaults)
NUM_PARTITIONS = int(os.environ.get("SPARK_JDBC_PARTITIONS", "8"))
FETCH_SIZE = os.environ.get("SPARK_JDBC_FETCHSIZE", "10000")

JDBC_URL = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"

TX_TABLE = "transactions_transaction"
OUT_TABLE = "transactions_monthlycategoryreport"

def log(msg: str) -> None:
    print(f"[spark_job] {msg}", flush=True)

spark = (
    SparkSession.builder
    .appName("monthly_category_report")
    .getOrCreate()
)

# Make Spark less eager to blow up driver memory on small local runs
spark.conf.set("spark.sql.shuffle.partitions", str(max(NUM_PARTITIONS, 8)))

# Build SQL source: filter expense in SQL (smaller read)
where_clauses = ["kind = 'expense'"]
if REPORT_YEAR and REPORT_MONTH:
    y = int(REPORT_YEAR)
    m = int(REPORT_MONTH)

    log(f"Mode: MONTHLY_REFRESH year={y} month={m:02d}")
    log(f"Deleting existing rows for {y}-{m:02d} from {OUT_TABLE}")

    delete_period_from_output_table(y, m)

    log(f"Computing aggregates for {y}-{m:02d}")
else:
    log("Mode: FULL_REFRESH (all months)")
    log(f"Truncating output table {OUT_TABLE}")

    truncate_output_table()

    log("Computing aggregates for all months")

where_sql = " AND ".join(where_clauses)
TX_SRC = f"(SELECT id, user_id, category_id, amount, date FROM {TX_TABLE} WHERE {where_sql}) AS tx"

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

# Compute bounds for partitioning (min/max id) from the *same filtered* dataset
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

# Extract year/month (Spark-side)
df = df.withColumn("year", F.year(F.col("date"))).withColumn("month", F.month(F.col("date")))

agg = (
    df.groupBy("user_id", "category_id", "year", "month")
    .agg(
        F.sum(F.col("amount")).alias("total_amount"),
        F.avg(F.col("amount")).alias("avg_amount"),
        F.count(F.lit(1)).alias("tx_count"),
    )
    .withColumn("computed_at", F.current_timestamp())
)

# Output strategy:
# - Full refresh: overwrite+truncate is fine for faks and simplest.
# - If you run per-month (REPORT_YEAR/MONTH), overwrite+truncate would wipe other months.
#   So: when period is specified, we append to a staging table OR do per-period upsert.
#   For simplicity + robustness: we do:
#     - full refresh if no REPORT_* provided
#     - per-period: delete that period rows first, then append (via JDBC execute is awkward in Spark)
#
# We'll implement:
#   - Full refresh: overwrite+truncate (safe)
#   - Per-period: write to a temp table and then you can merge in SQL (optional)
#
# To keep it self-contained and robust without adding DB-side merge code:
#   We'll *not* truncate when period is specified; we append results.
#   Risk: duplicates if you rerun same period.
#   Fix: you can later add an UPSERT (Phase 3 with Airflow can run a SQL task).
#
# For now, safest for your current stage: do full refresh always.
# If you *want* period mode now, tell me and I'll add a clean MERGE step via psycopg2.

write_mode = "overwrite"
truncate = "true"

log(f"Truncating output table {OUT_TABLE} (full refresh)")
truncate_output_table()

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
