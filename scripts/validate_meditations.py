#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "meditations.json"
REPORT_PATH = ROOT / "data" / "validation_report.json"


def expected_month_days(include_leap_day: bool = True) -> list[str]:
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)
    days: list[str] = []
    current = start
    while current <= end:
        if include_leap_day or current.strftime("%m-%d") != "02-29":
            days.append(current.strftime("%m-%d"))
        current += timedelta(days=1)
    return days


def validate(records: list[dict[str, str]]) -> dict[str, object]:
    keys = [record["month_day"] for record in records]
    counts = Counter(keys)
    expected = set(expected_month_days(include_leap_day=True))
    present = set(keys)

    return {
        "total_records": len(records),
        "unique_month_days": len(present),
        "has_leap_day": "02-29" in present,
        "duplicates": sorted(key for key, count in counts.items() if count > 1),
        "missing": sorted(expected - present),
        "unexpected": sorted(present - expected),
        "empty_title": sorted(record["month_day"] for record in records if not record.get("title")),
        "empty_body": sorted(record["month_day"] for record in records if not record.get("body")),
        "empty_reflection": sorted(record["month_day"] for record in records if not record.get("reflection")),
    }


def main() -> None:
    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    report = validate(records)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

