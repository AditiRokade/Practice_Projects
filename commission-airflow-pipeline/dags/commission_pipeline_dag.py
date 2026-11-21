from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.commission_pipeline import (
    publish_summary,
    reconcile_commissions,
    transform_commissions,
    validate_input,
)

PROJECT_ROOT = Path("/opt/airflow/project")
INPUT_PATH = PROJECT_ROOT / "data" / "commission_input.csv"
TRANSFORMED_PATH = PROJECT_ROOT / "artifacts" / "commission_transformed.csv"
SUMMARY_PATH = PROJECT_ROOT / "artifacts" / "commission_summary.json"


def validate_batch() -> int:
    return validate_input(INPUT_PATH)


def transform_batch() -> str:
    return transform_commissions(INPUT_PATH, TRANSFORMED_PATH)


def reconcile_batch() -> dict:
    return reconcile_commissions(TRANSFORMED_PATH)


def publish_batch() -> str:
    return publish_summary(TRANSFORMED_PATH, SUMMARY_PATH)


with DAG(
    dag_id="commission_reconciliation",
    description="Validate, calculate, reconcile, and publish a synthetic commission batch.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["portfolio", "data-quality", "finance"],
) as dag:
    validate_task = PythonOperator(
        task_id="validate_input",
        python_callable=validate_batch,
    )
    transform_task = PythonOperator(
        task_id="calculate_commissions",
        python_callable=transform_batch,
    )
    reconcile_task = PythonOperator(
        task_id="reconcile_payouts",
        python_callable=reconcile_batch,
    )
    publish_task = PythonOperator(
        task_id="publish_summary",
        python_callable=publish_batch,
    )

    validate_task >> transform_task >> reconcile_task >> publish_task
