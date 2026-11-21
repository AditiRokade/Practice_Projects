from pyspark.sql import DataFrame
from pyspark.sql import functions as F

REQUIRED_COLUMNS = {
    "event_id",
    "subscriber_id",
    "event_ts",
    "event_type",
    "duration_seconds",
    "amount",
    "country",
}


def _clean_text(column_name: str):
    value = F.trim(F.col(column_name))
    missing_markers = ["", "NULL", "N/A", "NA", "NONE", "UNKNOWN"]
    return F.when(F.upper(value).isin(*missing_markers), F.lit(None)).otherwise(value)


def clean_events(events: DataFrame) -> DataFrame:
    missing = REQUIRED_COLUMNS.difference(events.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    normalized = events.select(
        _clean_text("event_id").alias("event_id"),
        _clean_text("subscriber_id").alias("subscriber_id"),
        F.expr("try_to_timestamp(event_ts)").alias("event_ts"),
        F.lower(_clean_text("event_type")).alias("event_type"),
        F.expr("try_cast(duration_seconds AS INT)").alias("duration_seconds"),
        F.expr("try_cast(amount AS DOUBLE)").alias("amount"),
        F.upper(_clean_text("country")).alias("country"),
    )
    normalized = normalized.withColumn(
        "event_type",
        F.when(F.col("event_type").isin("call", "voice_call"), "voice")
        .when(F.col("event_type").isin("text", "text_message"), "sms")
        .when(F.col("event_type") == "data_session", "data")
        .otherwise(F.col("event_type")),
    )

    valid = normalized.filter(
        F.col("event_id").isNotNull()
        & (F.col("event_id") != "")
        & F.col("subscriber_id").isNotNull()
        & (F.col("subscriber_id") != "")
        & F.col("event_ts").isNotNull()
        & F.col("duration_seconds").isNotNull()
        & (F.col("duration_seconds") >= 0)
        & F.col("amount").isNotNull()
        & (F.col("amount") >= 0)
        & F.col("event_type").isNotNull()
        & F.col("event_type").isin("voice", "sms", "data")
        & F.col("country").isNotNull()
        & F.col("country").rlike("^[A-Z]{2}$")
        & ~F.isnan(F.col("amount"))
        & (F.abs(F.col("amount")) != float("inf"))
    )

    return (
        valid.dropDuplicates(["event_id"])
        .withColumn("event_date", F.to_date("event_ts"))
    )
