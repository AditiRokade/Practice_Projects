import argparse

from pyspark.sql import SparkSession

from src.transform import clean_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean synthetic telecom events into partitioned Parquet.")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output Parquet directory")
    args = parser.parse_args()

    spark = SparkSession.builder.appName("telecom-lakehouse-local").getOrCreate()
    try:
        events = spark.read.option("header", True).csv(args.input)
        clean_events(events).write.mode("overwrite").partitionBy("event_date").parquet(args.output)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
