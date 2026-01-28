import uuid
from datetime import datetime, timezone
import requests

AIRFLOW_BASE = "http://airflow-api-server:8080"
AIRFLOW_API = f"{AIRFLOW_BASE}/api/v2"
AIRFLOW_USER = "admin"
AIRFLOW_PASS = "admin"

def get_airflow_jwt() -> str:
    r = requests.post(
        f"{AIRFLOW_BASE}/auth/token",
        json={"username": AIRFLOW_USER, "password": AIRFLOW_PASS},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def trigger_airflow_dag(dag_id: str, conf: dict | None = None):
    token = get_airflow_jwt()
    url = f"{AIRFLOW_API}/dags/{dag_id}/dagRuns"

    logical_date = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    payload = {
        "dag_run_id": f"django__{uuid.uuid4()}",
        "logical_date": logical_date, 
        "conf": conf or {},
    }

    r = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()
