from __future__ import annotations

from datetime import datetime
import pendulum

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

try:
    from airflow.providers.docker.operators.docker import DockerOperator
    HAS_DOCKER_OP = True
except Exception:
    HAS_DOCKER_OP = False


TZ = pendulum.timezone("UTC")

with DAG(
    dag_id="montra_warm_exchange_rates",
    start_date=datetime(2026, 1, 1, tzinfo=TZ),
    schedule="0 */8 * * *",
    catchup=False,
    tags=["montra", "redis", "exchange-rates"],
) as dag:

    warm_rates = DockerOperator(
        task_id="warm_rates",
        image="montra-web",
        command=["python", "manage.py", "warm_exchange_rates", "--base", "EUR"],
        docker_url="unix://var/run/docker.sock",
        network_mode="montra_net",
        auto_remove="success",
        tty=True,
        mount_tmp_dir=False,
        environment={
            "REDIS_URL": "redis://redis:6379/1",
        },
    )

with DAG(
    dag_id="montra_monthly_spark_report",
    start_date=datetime(2026, 1, 1, tzinfo=TZ),
    schedule="@monthly",
    catchup=False,
    tags=["montra", "spark", "reports"],
) as dag_spark:

    report_year = "{{ (data_interval_start - macros.dateutil.relativedelta.relativedelta(months=1)).year }}"
    report_month = "{{ (data_interval_start - macros.dateutil.relativedelta.relativedelta(months=1)).month }}"

    if HAS_DOCKER_OP:
        run_spark = DockerOperator(
            task_id="run_spark_monthly_report",
            image="montra-spark_job",
            api_version="auto",
            auto_remove="success",
            docker_url="unix://var/run/docker.sock",
            network_mode="montra_net",
            environment={
                "POSTGRES_HOST": "db",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "montra_db",
                "POSTGRES_USER": "montra_user",
                "POSTGRES_PASSWORD": "montra_pass",
                "REPORT_YEAR": report_year,
                "REPORT_MONTH": report_month,
            },
            command="/opt/spark/bin/spark-submit /opt/app/spark_jobs/monthly_category_report.py",
        )
    else:
        run_spark = BashOperator(
            task_id="run_spark_monthly_report",
            bash_command=(
                "docker compose run --rm "
                f'-e REPORT_YEAR="{report_year}" -e REPORT_MONTH="{report_month}" '
                "spark_job"
            ),
        )
