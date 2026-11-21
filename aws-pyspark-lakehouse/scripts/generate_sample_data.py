import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path

COLUMNS = [
    "event_id",
    "subscriber_id",
    "event_ts",
    "event_type",
    "duration_seconds",
    "amount",
    "country",
]
EVENT_TYPES = ["voice", "sms", "data"]
COUNTRIES = ["IN", "GB", "US", "CA", "AU"]


def _event_row(number: int) -> list[str]:
    event_type = EVENT_TYPES[(number - 1) % len(EVENT_TYPES)]
    event_time = datetime(2026, 3, 1, 0, 0) + timedelta(minutes=number * 9)
    duration = 0 if event_type == "sms" else 15 + ((number * 37) % 600)
    amount_cents = 10 + ((number * 47) % 1_790)
    row = [
        f"E-{1_000_000 + number}",
        f"S-{100 + ((number * 17) % 2_500):04d}",
        event_time.strftime("%Y-%m-%d %H:%M:%S"),
        event_type,
        str(duration),
        f"{amount_cents // 100}.{amount_cents % 100:02d}",
        COUNTRIES[(number - 1) % len(COUNTRIES)],
    ]

    if number % 7 == 0:
        row[0] = f" {row[0]} "
    if number % 11 == 0:
        row[1] = f" {row[1]} "
    if number % 17 == 0:
        row[3] = {"voice": " CALL ", "sms": "TEXT_MESSAGE", "data": "data_session"}[event_type]
    elif number % 13 == 0:
        row[3] = f" {event_type.upper()} "
    if number % 19 == 0:
        row[6] = f" {row[6].lower()} "

    if number % 101 == 0:
        row[0] = "N/A"
    if number % 113 == 0:
        row[2] = "not-a-timestamp"
    if number % 97 == 0:
        row[4] = "many"
    elif number % 89 == 0:
        row[4] = "-15"
    if number % 103 == 0:
        row[5] = "N/A"
    elif number % 83 == 0:
        row[5] = "-2.50"
    if number % 127 == 0:
        row[3] = "mms"
    if number % 137 == 0:
        row[6] = "??"
    if number % 139 == 0:
        row[1] = "NULL"
    return row


def generate_sample(output_path: Path, row_count: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(COLUMNS)
        previous_row: list[str] | None = None
        for number in range(1, row_count + 1):
            row = _event_row(number)
            if number % 47 == 0 and previous_row is not None:
                row = previous_row.copy()
            writer.writerow(row)
            previous_row = row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic telecom events.")
    parser.add_argument("--rows", type=int, default=1500, help="Number of raw event rows")
    parser.add_argument("--output", type=Path, default=Path("data/raw/telecom_events.csv"))
    args = parser.parse_args()
    if args.rows < 1500:
        parser.error("--rows must be at least 1500")

    generate_sample(args.output, args.rows)
    print(f"Generated {args.rows} telecom event rows in {args.output}")


if __name__ == "__main__":
    main()
