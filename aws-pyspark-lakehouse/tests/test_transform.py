import unittest
from pathlib import Path

from pyspark.sql import SparkSession

from src.transform import clean_events


class CleanEventsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spark = (
            SparkSession.builder.master("local[1]")
            .appName("test-telecom-transform")
            .getOrCreate()
        )
        cls.spark.sparkContext.setLogLevel("ERROR")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.spark.stop()

    def test_normalizes_deduplicates_and_rejects_invalid_rows(self) -> None:
        rows = [
            (" E-1 ", " S-1 ", "2026-03-01 09:00:00", " VOICE ", "30", "1.5", "in"),
            ("E-1", "S-1", "2026-03-01 09:00:00", "VOICE", "30", "1.5", "in"),
            ("E-2", "", "2026-03-01 09:01:00", "sms", "0", "0.1", "in"),
            ("E-3", "S-3", "2026-03-01 09:02:00", "data", "-1", "0.2", "gb"),
            ("E-4", "S-4", "not-a-date", "voice", "20", "0.2", "in"),
            ("E-5", "S-5", "2026-03-01 09:04:00", "voice", "many", "0.2", "in"),
            ("E-6", "S-6", "2026-03-01 09:05:00", "sms", "0", "N/A", "in"),
            ("E-7", "S-7", "2026-03-01 09:06:00", "mms", "0", "0.2", "in"),
            ("E-8", "S-8", "2026-03-01 09:07:00", "data", "10", "0.2", "??"),
            ("E-9", "NULL", "2026-03-01 09:08:00", "data", "10", "0.2", "in"),
            (" E-10 ", " S-10 ", "2026-03-01 09:09:00", " CALL ", "15", "0.3", "gb"),
        ]
        columns = [
            "event_id",
            "subscriber_id",
            "event_ts",
            "event_type",
            "duration_seconds",
            "amount",
            "country",
        ]
        source = self.spark.createDataFrame(rows, columns)

        result = clean_events(source).collect()

        self.assertEqual(len(result), 2)
        cleaned = {row["event_id"]: row for row in result}
        self.assertEqual(cleaned["E-1"]["subscriber_id"], "S-1")
        self.assertEqual(cleaned["E-1"]["event_type"], "voice")
        self.assertEqual(cleaned["E-1"]["country"], "IN")
        self.assertEqual(cleaned["E-10"]["event_type"], "voice")
        self.assertEqual(str(cleaned["E-1"]["event_date"]), "2026-03-01")

    def test_missing_columns_raise_clear_error(self) -> None:
        source = self.spark.createDataFrame([], ["event_id"])
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            clean_events(source)

    def test_1500_row_sample_cleans_to_unique_events(self) -> None:
        sample_path = Path(__file__).parents[1] / "data" / "raw" / "telecom_events.csv"
        source = self.spark.read.option("header", True).csv(str(sample_path))
        self.assertEqual(source.count(), 1500)

        cleaned = clean_events(source)
        cleaned_count = cleaned.count()
        self.assertGreater(cleaned_count, 1200)
        self.assertLess(cleaned_count, 1500)
        self.assertEqual(cleaned_count, cleaned.select("event_id").distinct().count())


if __name__ == "__main__":
    unittest.main()
