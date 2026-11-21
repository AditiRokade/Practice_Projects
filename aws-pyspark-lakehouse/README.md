# AWS Telecom Lakehouse: PySpark Batch Transform

A reproducible portfolio implementation of a Bronze-to-Silver telecom event transform. It includes 1,500 synthetic CSV rows with duplicates, missing-value markers, malformed timestamps and numbers, invalid measures, mixed casing, and unsupported categories. It runs locally with PySpark; AWS resources are not provisioned by this repository.

## What it demonstrates

- Trimming and normalizing text, placeholder nulls, event aliases, timestamps, and numeric fields.
- Rejecting malformed timestamps/numbers, missing identifiers, negative measures, unknown event types, and invalid country codes.
- Writing Parquet partitioned by event date, ready for cataloging and Athena-style analytics.
- Unit tests for valid, duplicate, and rejected records.
- A deterministic generator for rebuilding the 1,500-row sample.

## Run locally

Requirements: Python 3.10+ and Java 17+ (required by Spark).

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_sample_data.py
python -m src.run_pipeline --input data/raw/telecom_events.csv --output data/processed/events
python -m unittest discover -s tests -v
```

The output directory is ignored by Git. Inspect it with Spark or a compatible Parquet reader.

## Layout

- `data/raw/telecom_events.csv`: 1,500 synthetic input records with both cleanable and rejected records.
- `scripts/generate_sample_data.py`: deterministic sample-data generator (`--rows` accepts values of at least 1,500).
- `src/transform.py`: transformations that can be reused by a Glue job.
- `src/run_pipeline.py`: local Spark entry point.
- `tests/`: behavior checks for transformation rules.

## Cloud adaptation

For an AWS deployment, replace local paths with S3 locations, provide the Glue/Spark runtime, register the output with Glue Data Catalog, and add Lake Formation permissions. This repo does not create AWS infrastructure or claim measured production performance. Do not put credentials or real subscriber data in Git.
