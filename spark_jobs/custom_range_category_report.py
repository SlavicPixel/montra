import os
import sys
import uuid
from datetime import datetime, timezone
from pyspark.sql import SparkSession, functions as F
import psycopg2


def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[spark_job] {ts} | {msg}", flush=True)


PG_HOST = os.environ.get("POSTGRES_HOST", "db")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ.get("POSTGRES_DB", "montra_db")
PG_USER = os.environ.get("POSTGRES_USER", "montra_user")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "montra_pass")

# Custom params from Airflow
REPORT_USER_ID = os.environ.get("REPORT_USER_ID")  # required
REQUEST_ID = os.environ.get("REQUEST_ID")          # required (uuid string)
DATE_FROM = os.environ.get("DATE_FROM")            # required "YYYY-MM-DD"
DATE_TO = os.environ.get("DATE_TO")                # required "YYYY-MM-DD"

# Tuning knobs
NUM_PARTITIONS = int(os.environ.get("SPARK_JDBC_PARTITIONS", "8"))
FETCH_SIZE = os.environ.get("SPARK_JDBC_FETCHSIZE", "10000")

JDBC_URL = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"

TX_TABLE = "transactions_transaction"
OUT_TABLE = "transactions_customrangecategoryreport"


def _require_env(name: str, value):
    if not value:
        log(f"Missing required env var: {name}")
        sys.exit(2)


def delete_request_from_output_table(request_uuid: uuid.UUID, user_id: int):
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
            f"DELETE FROM {OUT_TABLE} WHERE request_id = %s AND user_id = %s;",
            (str(request_uuid), user_id),
        )
    conn.close()


def insert_rows(request_uuid: uuid.UUID, user_id: int, date_from: str, date_to: str, rows):
    """
    rows: list of dicts: {category_id, total_amount, avg_amount, tx_count, computed_at}
    """
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        sql = f"""
        INSERT INTO {OUT_TABLE}
            (request_id, user_id, category_id, date_from, date_to,
             total_amount, avg_amount, tx_count, computed_at)
        VALUES
            (%s::uuid, %s, %s, %s::date, %s::date,
             %s, %s, %s, %s);
        """
        data = []
        for r in rows:
            data.append((
                str(request_uuid),
                user_id,
                int(r["category_id"]),
                date_from,
                date_to,
                r["total_amount"],
                r["avg_amount"],
                int(r["tx_count"]),
                r["computed_at"],
            ))
        if data:
            cur.executemany(sql, data)
    conn.close()


def main():
    _require_env("REPORT_USER_ID", REPORT_USER_ID)
    _require_env("REQUEST_ID", REQUEST_ID)
    _require_env("DATE_FROM", DATE_FROM)
    _require_env("DATE_TO", DATE_TO)

    user_id = int(REPORT_USER_ID)
    request_uuid = uuid.UUID(REQUEST_ID)

    log(f"Mode: CUSTOM_RANGE request_id={request_uuid} user_id={user_id} range={DATE_FROM}..{DATE_TO}")
    log(f"Output table: {OUT_TABLE}")

    spark = (
        SparkSession.builder
        .appName("custom_range_category_report")
        .getOrCreate()
    )
    spark.conf.set("spark.sql.shuffle.partitions", str(max(NUM_PARTITIONS, 8)))

    # Filter in SQL (read less)
    # NOTE: date range inclusive -> inclusive: date >= from and date <= to
    where_clauses = [
        "kind = 'expense'",
        f"user_id = {user_id}",
        f"date >= DATE '{DATE_FROM}'",
        f"date <= DATE '{DATE_TO}'",
    ]
    where_sql = " AND ".join(where_clauses)

    tx_src = f"(SELECT id, user_id, category_id, amount, date FROM {TX_TABLE} WHERE {where_sql}) AS tx"
    bounds_src = f"(SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM {TX_TABLE} WHERE {where_sql}) AS b"

    log(f"Reading source: {tx_src}")
    log(f"JDBC fetchsize={FETCH_SIZE}, partitions={NUM_PARTITIONS}")

    base_reader = (
        spark.read.format("jdbc")
        .option("url", JDBC_URL)
        .option("dbtable", tx_src)
        .option("user", PG_USER)
        .option("password", PG_PASS)
        .option("driver", "org.postgresql.Driver")
        .option("fetchsize", str(FETCH_SIZE))
    )

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

    # Idempotent delete first (so reruns are clean even if no data)
    log("Deleting existing rows for this request/user (idempotent refresh)")
    delete_request_from_output_table(request_uuid, user_id)

    if min_id is None or max_id is None:
        log("No matching transactions found for this range. (Deleted old rows.) Exiting OK.")
        spark.stop()
        return

    log(f"Partition bounds: id {min_id}..{max_id}")

    df = (
        base_reader
        .option("partitionColumn", "id")
        .option("lowerBound", str(min_id))
        .option("upperBound", str(max_id))
        .option("numPartitions", str(NUM_PARTITIONS))
        .load()
    )

    agg = (
        df.groupBy("category_id")
        .agg(
            F.sum(F.col("amount")).alias("total_amount"),
            F.avg(F.col("amount")).alias("avg_amount"),
            F.count(F.lit(1)).alias("tx_count"),
        )
        .withColumn("computed_at", F.current_timestamp())
        .select("category_id", "total_amount", "avg_amount", "tx_count", "computed_at")
    )

    result_rows = [r.asDict() for r in agg.collect()]
    log(f"Computed {len(result_rows)} category rows. Inserting...")

    insert_rows(
        request_uuid=request_uuid,
        user_id=user_id,
        date_from=DATE_FROM,
        date_to=DATE_TO,
        rows=result_rows,
    )

    log("Done.")
    spark.stop()


if __name__ == "__main__":
    main()
