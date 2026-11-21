import csv
import tempfile
import unittest
from pathlib import Path

from src.commission_pipeline import (
    publish_summary,
    reconcile_commissions,
    transform_commissions,
    validate_input,
)


class CommissionPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.input_path = self.root / "input.csv"
        self.transformed_path = self.root / "output" / "transformed.csv"
        self._write_rows(
            [
                ["TX-1", "AG-1", "100.00", "0.0500", "5.00"],
                ["TX-2", "AG-1", "200.00", "0.0750", "15.00"],
            ]
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_rows(self, rows: list[list[str]]) -> None:
        with self.input_path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(
                ["transaction_id", "agent_id", "gross_amount", "commission_rate", "payout_amount"]
            )
            writer.writerows(rows)

    def test_valid_batch_calculates_and_publishes_summary(self) -> None:
        self.assertEqual(validate_input(self.input_path), 2)
        transform_commissions(self.input_path, self.transformed_path)
        result = reconcile_commissions(self.transformed_path)
        summary_path = self.root / "summary.json"
        publish_summary(self.transformed_path, summary_path)

        self.assertTrue(result["reconciled"])
        self.assertEqual(result["expected_total"], "20.00")
        self.assertEqual(result["agent_count"], 1)
        self.assertTrue(summary_path.exists())

    def test_reconciliation_blocks_mismatched_payout(self) -> None:
        self._write_rows([["TX-1", "AG-1", "100.00", "0.0500", "5.50"]])
        transform_commissions(self.input_path, self.transformed_path)

        with self.assertRaisesRegex(ValueError, "Payout reconciliation failed"):
            reconcile_commissions(self.transformed_path)

    def test_reconciliation_blocks_cumulative_batch_variance(self) -> None:
        self._write_rows(
            [
                ["TX-1", "AG-1", "100.00", "0.0500", "5.01"],
                ["TX-2", "AG-1", "100.00", "0.0500", "5.01"],
            ]
        )
        transform_commissions(self.input_path, self.transformed_path)

        with self.assertRaisesRegex(ValueError, "Total payout variance"):
            reconcile_commissions(self.transformed_path)

    def test_duplicate_transaction_id_is_rejected(self) -> None:
        self._write_rows(
            [
                ["TX-1", "AG-1", "100.00", "0.0500", "5.00"],
                ["TX-1", "AG-2", "200.00", "0.0750", "15.00"],
            ]
        )

        with self.assertRaisesRegex(ValueError, "Duplicate transaction_id"):
            validate_input(self.input_path)

    def test_currency_format_percentage_and_whitespace_are_normalized(self) -> None:
        self._write_rows([[" TX-1 ", " AG-1 ", "$1,000.00", "5%", " $50.00 "]])
        self.assertEqual(validate_input(self.input_path), 1)
        transform_commissions(self.input_path, self.transformed_path)

        with self.transformed_path.open(newline="", encoding="utf-8") as source:
            row = next(csv.DictReader(source))
        self.assertEqual(row["transaction_id"], "TX-1")
        self.assertEqual(row["agent_id"], "AG-1")
        self.assertEqual(row["gross_amount"], "1000.00")
        self.assertEqual(row["expected_payout"], "50.00")

    def test_generated_1500_row_batch_validates(self) -> None:
        sample_path = Path(__file__).parents[1] / "data" / "commission_input.csv"
        self.assertEqual(validate_input(sample_path), 1500)
        transform_commissions(sample_path, self.transformed_path)
        summary = reconcile_commissions(self.transformed_path)
        self.assertEqual(summary["row_count"], 1500)
        self.assertEqual(summary["variance_total"], "0.00")

    def test_invalid_sample_batch_is_rejected(self) -> None:
        invalid_path = Path(__file__).parents[1] / "data" / "commission_invalid_rows.csv"
        with self.assertRaisesRegex(ValueError, "Invalid gross_amount"):
            validate_input(invalid_path)


if __name__ == "__main__":
    unittest.main()
