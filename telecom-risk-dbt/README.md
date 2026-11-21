# Telecom Risk Analytics: dbt + DuckDB

A local analytics engineering project that turns synthetic telecom events into subscriber-day risk features and a reviewable alert mart. It is designed to run without a cloud account.

## What it demonstrates

- dbt staging, intermediate, and mart models with explicit casts and readable SQL.
- DuckDB as a zero-service local warehouse.
- Seed data, model-level tests, and singular SQL data tests.
- A transparent heuristic score that is easy to explain and tune.

## Run locally

Requirements: Python 3.10+.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
dbt build --project-dir . --profiles-dir .
dbt docs generate --project-dir . --profiles-dir .
```

Open `target/index.html` after docs generation. The database is created under `target/` and is ignored by Git.

## Risk rule

The mart labels a subscriber-day HIGH when there are at least 3 events, or spend is at least 75 and at least 2 event types are present. It labels a day MEDIUM at spend of at least 35; otherwise LOW. This is a demonstration heuristic, not a trained fraud model or a claim about real fraud outcomes.

## Layout

- `seeds/telecom_events.csv`: fully synthetic, intentionally small events.
- `models/staging/`: typed and normalized event records.
- `models/intermediate/`: subscriber-day aggregates.
- `models/marts/`: risk features and alert category.
- `tests/`: SQL assertions for keys and nonnegative measures.

## Cloud adaptation

The model logic can be adapted to BigQuery by changing the dbt adapter and profile. Streaming ingestion, Pub/Sub, Dataflow, IAM, and alert delivery are intentionally outside this local repo. No cloud resources or performance benchmarks are provisioned here.
