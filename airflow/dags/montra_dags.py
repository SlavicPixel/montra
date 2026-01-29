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
    dag_id="montra_monthly_spark_report_current_month",
    start_date=datetime(2026, 1, 1, tzinfo=TZ),
    schedule="*/15 * * * *",   # svakih 15 min
    catchup=False,
    tags=["montra", "spark", "reports"],
) as dag:

    report_year = "{{ data_interval_start.year }}"
    report_month = "{{ data_interval_start.month }}"

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
            mount_tmp_dir=False,
        )
    else:
        run_spark = BashOperator(
            task_id="run_spark_monthly_report",
            bash_command=(
                "docker compose run --rm "
                f'-e REPORT_YEAR="{report_year}" '
                f'-e REPORT_MONTH="{report_month}" '
                "-e POSTGRES_HOST=db "
                "-e POSTGRES_PORT=5432 "
                "-e POSTGRES_DB=montra_db "
                "-e POSTGRES_USER=montra_user "
                "-e POSTGRES_PASSWORD=montra_pass "
                "spark_job"
            ),
        )

with DAG(
    dag_id="montra_monthly_spark_report_full_refresh",
    start_date=datetime(2026, 1, 1, tzinfo=TZ),
    schedule="5 2 * * *",   # svaki dan u 02:15
    catchup=False,
    tags=["montra", "spark", "reports"],
) as dag:

    if HAS_DOCKER_OP:
        run_spark = DockerOperator(
            task_id="run_spark_monthly_report_full_refresh",
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
            },
            command="/opt/spark/bin/spark-submit /opt/app/spark_jobs/monthly_category_report.py",
            mount_tmp_dir=False,
        )
    else:
        run_spark = BashOperator(
            task_id="run_spark_monthly_report_full_refresh",
            bash_command=(
                "docker compose run --rm "
                "-e POSTGRES_HOST=db "
                "-e POSTGRES_PORT=5432 "
                "-e POSTGRES_DB=montra_db "
                "-e POSTGRES_USER=montra_user "
                "-e POSTGRES_PASSWORD=montra_pass "
                "spark_job"
            ),
        )

with DAG(
    dag_id="montra_yearly_spark_report",
    start_date=datetime(2026, 1, 1, tzinfo=TZ),
    schedule="0 * * * *",  # svaki sat
    catchup=False,
    tags=["montra", "spark", "reports", "yearly"],
) as dag:

    report_year = "{{ dag_run.conf.get('year', data_interval_start.year) }}"
    report_user_id = "{{ dag_run.conf.get('user_id', '') }}"

    run_spark = DockerOperator(
        task_id="run_spark_yearly_report",
        image="montra-spark_job",
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
            "REPORT_USER_ID": report_user_id,
        },
        command="/opt/spark/bin/spark-submit /opt/app/spark_jobs/yearly_category_report.py",
    )

with DAG(
    dag_id="montra_custom_range_spark_report",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["montra", "spark", "reports", "custom-range"],
) as dag:

    report_user_id = "{{ dag_run.conf.get('user_id') }}"
    request_id = "{{ dag_run.conf.get('request_id') }}"
    date_from = "{{ dag_run.conf.get('date_from') }}"
    date_to = "{{ dag_run.conf.get('date_to') }}"

    run_spark = DockerOperator(
        task_id="run_spark_custom_range_report",
        image="montra-spark_job",
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        network_mode="montra_net",
        mount_tmp_dir=False,
        environment={
            "POSTGRES_HOST": "db",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "montra_db",
            "POSTGRES_USER": "montra_user",
            "POSTGRES_PASSWORD": "montra_pass",
            "REPORT_USER_ID": report_user_id,
            "REQUEST_ID": request_id,
            "DATE_FROM": date_from,
            "DATE_TO": date_to,
        },
        command="/opt/spark/bin/spark-submit /opt/app/spark_jobs/custom_range_category_report.py",
    )
