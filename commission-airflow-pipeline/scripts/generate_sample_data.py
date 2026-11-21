import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

COLUMNS = [
    "transaction_id",
    "agent_id",
    "gross_amount",
    "commission_rate",
    "payout_amount",
]
CENT = Decimal("0.01")
RATES = [Decimal("0.035"), Decimal("0.040"), Decimal("0.050"), Decimal("0.060"), Decimal("0.075"), Decimal("0.080")]


def _main_row(number: int) -> list[str]:
    gross_cents = 50_000 + ((number * 7_919) % 950_000)
    gross = Decimal(gross_cents) / Decimal("100")
    rate = RATES[(number - 1) % len(RATES)]
    payout = (gross * rate).quantize(CENT, rounding=ROUND_HALF_UP)
    agent_number = 101 + ((number * 7) % 25)

    transaction_id = f"TX-{number:06d}"
    agent_id = f"AG-{agent_number:03d}"
    gross_text = f"${gross:,.2f}" if number % 17 == 0 else f"{gross:.2f}"
    rate_text = f"{rate * 100:.2f}%" if number % 23 == 0 else f"{rate:.4f}"
    payout_text = f"${payout:,.2f}" if number % 29 == 0 else f"{payout:.2f}"

    if number % 7 == 0:
        transaction_id = f" {transaction_id} "
    if number % 11 == 0:
        agent_id = f" {agent_id} "
    if number % 13 == 0 and number % 17 != 0:
        gross_text = f" {gross_text} "
    if number % 19 == 0:
        payout_text = f" {payout_text} "

    return [transaction_id, agent_id, gross_text, rate_text, payout_text]


def generate_main_batch(output_path: Path, row_count: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(COLUMNS)
        for number in range(1, row_count + 1):
            writer.writerow(_main_row(number))


def generate_invalid_rows(output_path: Path) -> None:
    rows = [
        ["TX-BAD-001", "AG-101", "N/A", "0.0500", "50.00"],
        ["TX-BAD-002", "AG-102", "1000.00", "150%", "1500.00"],
        ["TX-BAD-003", "AG-103", "-500.00", "0.0500", "-25.00"],
        ["", "AG-104", "250.00", "0.0400", "10.00"],
        ["TX-BAD-005", "UNKNOWN", "500.00", "0.0500", "25.00"],
        ["TX-BAD-006", "AG-106", "not-a-number", "0.0600", "30.00"],
        ["TX-BAD-007", "AG-107", "300.00", "0.0500", "N/A"],
        ["TX-BAD-008", "AG-108", "100.00", "0.0500", "5.50"],
        ["TX-BAD-008", "AG-108", "200.00", "0.0500", "10.00"],
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(COLUMNS)
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic commission pipeline fixtures.")
    parser.add_argument("--rows", type=int, default=1500, help="Number of cleanable commission rows")
    parser.add_argument("--output", type=Path, default=Path("data/commission_input.csv"))
    parser.add_argument("--invalid-output", type=Path, default=Path("data/commission_invalid_rows.csv"))
    args = parser.parse_args()
    if args.rows < 1500:
        parser.error("--rows must be at least 1500")

    generate_main_batch(args.output, args.rows)
    generate_invalid_rows(args.invalid_output)
    print(f"Generated {args.rows} commission rows in {args.output}")
    print(f"Generated invalid-row fixture in {args.invalid_output}")


if __name__ == "__main__":
    main()
