# Commission Pipeline: Airflow + Reconciliation

A portfolio-sized batch workflow that validates commission inputs, calculates expected payouts using decimal arithmetic, blocks publication when source payouts do not reconcile, and writes a summary. The main synthetic batch contains 1,500 transactions; a separate fixture contains invalid rows for demonstrating the quality gate.

## What it demonstrates

- An Airflow DAG with explicit validation, transformation, reconciliation, and publication tasks.
- Reusable standard-library business logic, independent of Airflow.
- Safe normalization for whitespace, currency symbols/grouping commas, and percent-formatted rates.
- Duplicate-key, schema, amount, rate, and payout checks; invalid financial values are rejected rather than silently coerced.
- Exact currency rounding with `Decimal` and tests for both passing and failing reconciliations.

## Run the logic tests

Requirements: Python 3.10+; no third-party packages are needed for these tests.

```powershell
py -m unittest discover -s tests -v
```

Regenerate both deterministic CSV fixtures with:

```powershell
python scripts/generate_sample_data.py
```

## Run the Airflow DAG with Docker

Requirements: Docker Desktop with Compose.

```powershell
docker compose up airflow
```

Open `http://localhost:8080`. `airflow standalone` creates a local admin account and prints the credentials in the container logs. Enable and trigger `commission_reconciliation` in the UI. Outputs are written to `artifacts/` and are ignored by Git.

## Layout

- `dags/commission_pipeline_dag.py`: Airflow orchestration.
- `src/commission_pipeline.py`: validation, transformation, reconciliation, and summary functions.
- `data/commission_input.csv`: 1,500 synthetic transactions, including safely normalizable formatting variations.
- `data/commission_invalid_rows.csv`: malformed rows that the validator should reject.
- `scripts/generate_sample_data.py`: deterministic fixture generator.
- `tests/`: standard-library unit tests.

## Production considerations

This local example does not connect to a bank, payroll system, cloud warehouse, or real Airflow service. A production deployment should use managed secrets, immutable source snapshots, idempotent output paths, access controls, and an audit store. No savings or SLA results are claimed by this repository.
