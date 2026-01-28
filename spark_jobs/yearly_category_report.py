import os
import sys
from datetime import datetime, timezone

import psycopg2
from pyspark.sql import SparkSession, functions as F


def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[spark_job] {ts} | {msg}", flush=True)


PG_HOST = os.environ.get("POSTGRES_HOST", "db")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ.get("POSTGRES_DB", "montra_db")
PG_USER = os.environ.get("POSTGRES_USER", "montra_user")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "montra_pass")

# Optional: run for a specific year; if missing -> FULL refresh (truncate)
REPORT_YEAR = os.environ.get("REPORT_YEAR")
# Optional: run only for a specific user (manual refresh from Django)
REPORT_USER_ID = os.environ.get("REPORT_USER_ID")

# Tuning knobs
NUM_PARTITIONS = int(os.environ.get("SPARK_JDBC_PARTITIONS", "8"))
FETCH_SIZE = os.environ.get("SPARK_JDBC_FETCHSIZE", "10000")

JDBC_URL = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"

TX_TABLE = "transactions_transaction"
OUT_TABLE = "transactions_yearlycategoryreport"


def _pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    )


def truncate_output_table():
    conn = _pg_conn()
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {OUT_TABLE} RESTART IDENTITY;")
    conn.close()


def delete_year_from_output_table(year: int, user_id=None):
    conn = _pg_conn()
    conn.autocommit = True
    with conn.cursor() as cur:
        if user_id is None:
            cur.execute(f"DELETE FROM {OUT_TABLE} WHERE year = %s;", (year,))
        else:
            cur.execute(
                f"DELETE FROM {OUT_TABLE} WHERE year = %s AND user_id = %s;",
                (year, user_id),
            )
    conn.close()


def parse_int_env(name: str, value: str):
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        raise ValueError(f"Invalid {name}={value!r}")


def main():
    y = parse_int_env("REPORT_YEAR", REPORT_YEAR)
    uid = parse_int_env("REPORT_USER_ID", REPORT_USER_ID)

    spark = (
        SparkSession.builder
        .appName("yearly_category_report")
        .getOrCreate()
    )

    spark.conf.set("spark.sql.shuffle.partitions", str(max(NUM_PARTITIONS, 8)))

    where_clauses = ["kind = 'expense'"]

    if y is not None:
        where_clauses.append(f"EXTRACT(YEAR FROM date) = {y}")

    if uid is not None:
        where_clauses.append(f"user_id = {uid}")

    where_sql = " AND ".join(where_clauses)
    TX_SRC = f"(SELECT id, user_id, category_id, amount, date FROM {TX_TABLE} WHERE {where_sql}) AS tx"

    if y is None:
        log("Mode: FULL_REFRESH (all years) " + ("(single-user)" if uid is not None else "(all users)"))
        log(f"Truncating output table {OUT_TABLE}")
        truncate_output_table()
    else:
        log(f"Mode: YEARLY_REFRESH year={y} user_id={'ALL' if uid is None else uid}")
        log(f"Deleting existing rows for year={y} user_id={'ALL' if uid is None else uid} from {OUT_TABLE}")
        delete_year_from_output_table(y, uid)

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

    bounds_src = f"(SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM {TX_TABLE} WHERE {where_sql}) AS b"

    bounds_row = (
        spark.read.format("jdbc")
        .option("url", JDBC_URL)
        .option("dbtable", bounds_src)
        .option("user", PG_USER)
        .option("password", PG_PASS)
        .option("driver", "org.postgresql.Driver")
        .load()
        .collect()[0]
    )

    min_id = bounds_row["min_id"]
    max_id = bounds_row["max_id"]

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

    df = df.withColumn("year", F.year(F.col("date")))

    agg = (
        df.groupBy("user_id", "category_id", "year")
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


if __name__ == "__main__":
    main()
