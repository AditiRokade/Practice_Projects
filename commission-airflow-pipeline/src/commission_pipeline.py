import csv
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = {
    "transaction_id",
    "agent_id",
    "gross_amount",
    "commission_rate",
    "payout_amount",
}
CENT = Decimal("0.01")
DEFAULT_TOLERANCE = Decimal("0.01")
MISSING_MARKERS = {"", "NULL", "N/A", "NA", "NONE", "UNKNOWN"}


def _parse_decimal(value: str | None, field_name: str, line_number: int) -> Decimal:
    normalized = (value or "").strip().replace(",", "").replace("$", "")
    is_percentage = field_name == "commission_rate" and normalized.endswith("%")
    if is_percentage:
        normalized = normalized[:-1].strip()
    try:
        number = Decimal(normalized)
        if not number.is_finite():
            raise InvalidOperation
        return number / Decimal("100") if is_percentage else number
    except InvalidOperation:
        raise ValueError(f"Invalid {field_name} on line {line_number}") from None


def _read_rows(input_path: str | Path) -> list[dict[str, str]]:
    with Path(input_path).open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fieldnames = [name.strip().lower() if name else "" for name in (reader.fieldnames or [])]
        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("Input contains duplicate column names")
        reader.fieldnames = fieldnames
        missing = REQUIRED_COLUMNS.difference(fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    if not rows:
        raise ValueError("Input contains no commission rows")

    seen_ids: set[str] = set()
    cleaned_rows: list[dict[str, str]] = []
    for line_number, row in enumerate(rows, start=2):
        transaction_id = (row["transaction_id"] or "").strip()
        agent_id = (row["agent_id"] or "").strip()
        if transaction_id.upper() in MISSING_MARKERS or agent_id.upper() in MISSING_MARKERS:
            raise ValueError(f"Missing transaction_id or agent_id on line {line_number}")
        if transaction_id in seen_ids:
            raise ValueError(f"Duplicate transaction_id {transaction_id}")
        seen_ids.add(transaction_id)
        gross_amount = _parse_decimal(row["gross_amount"], "gross_amount", line_number)
        commission_rate = _parse_decimal(row["commission_rate"], "commission_rate", line_number)
        payout_amount = _parse_decimal(row["payout_amount"], "payout_amount", line_number)
        if gross_amount < 0 or payout_amount < 0 or not Decimal("0") <= commission_rate <= Decimal("1"):
            raise ValueError(f"Out-of-range amount or commission rate on line {line_number}")
        cleaned_rows.append(
            {
                "transaction_id": transaction_id,
                "agent_id": agent_id,
                "gross_amount": f"{gross_amount:.2f}",
                "commission_rate": str(commission_rate),
                "payout_amount": f"{payout_amount:.2f}",
            }
        )

    return cleaned_rows


def validate_input(input_path: str | Path) -> int:
    return len(_read_rows(input_path))


def transform_commissions(input_path: str | Path, output_path: str | Path) -> str:
    rows = _read_rows(input_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "transaction_id",
        "agent_id",
        "gross_amount",
        "commission_rate",
        "payout_amount",
        "expected_payout",
        "variance",
    ]

    with destination.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            expected = (Decimal(row["gross_amount"]) * Decimal(row["commission_rate"])).quantize(
                CENT, rounding=ROUND_HALF_UP
            )
            paid = Decimal(row["payout_amount"]).quantize(CENT, rounding=ROUND_HALF_UP)
            writer.writerow(
                {
                    **row,
                    "expected_payout": f"{expected:.2f}",
                    "variance": f"{(paid - expected):.2f}",
                }
            )
    return str(destination)


def reconcile_commissions(
    transformed_path: str | Path,
    tolerance: Decimal = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    with Path(transformed_path).open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError("Transformed output contains no commission rows")

    expected_total = sum((Decimal(row["expected_payout"]) for row in rows), Decimal("0.00"))
    paid_total = sum((Decimal(row["payout_amount"]) for row in rows), Decimal("0.00"))
    variance_total = paid_total - expected_total
    mismatches = [row["transaction_id"] for row in rows if abs(Decimal(row["variance"])) > tolerance]
    if mismatches:
        raise ValueError(f"Payout reconciliation failed for: {', '.join(mismatches)}")
    if abs(variance_total) > tolerance:
        raise ValueError(f"Total payout variance {variance_total:.2f} exceeds tolerance {tolerance:.2f}")

    return {
        "row_count": len(rows),
        "agent_count": len({row["agent_id"] for row in rows}),
        "expected_total": f"{expected_total:.2f}",
        "paid_total": f"{paid_total:.2f}",
        "variance_total": f"{variance_total:.2f}",
        "reconciled": True,
    }


def publish_summary(transformed_path: str | Path, summary_path: str | Path) -> str:
    summary = reconcile_commissions(transformed_path)
    totals_by_agent: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    with Path(transformed_path).open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            totals_by_agent[row["agent_id"]] += Decimal(row["expected_payout"])

    summary["expected_by_agent"] = {
        agent_id: f"{amount:.2f}" for agent_id, amount in sorted(totals_by_agent.items())
    }
    destination = Path(summary_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return str(destination)
