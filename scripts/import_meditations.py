#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data"
REFLECTION_RE = re.compile(r"\bS[OÓ]\s+POR\s+HOJE\s*:", re.IGNORECASE)


def normalize_text(value: Any) -> str:
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    compact: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank and compact:
                compact.append("")
            blank = True
            continue
        compact.append(line)
        blank = False
    return "\n".join(compact).strip()


def parse_month_day(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%m-%d")
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime().strftime("%m-%d")

    raw = str(value).strip()
    if re.fullmatch(r"\d{2}-\d{2}", raw):
        return raw

    parsed = pd.to_datetime(raw)
    return parsed.strftime("%m-%d")


def split_meditation(text: str) -> tuple[str, str, str]:
    normalized = normalize_text(text)
    lines = normalized.split("\n")
    title = next((line.strip() for line in lines if line.strip()), "")
    if not title:
        raise ValueError("Meditacao sem titulo")

    title_index = lines.index(title)
    without_title = "\n".join(lines[title_index + 1 :]).strip()
    match = REFLECTION_RE.search(without_title)
    if not match:
        raise ValueError(f"Marcador 'So por hoje' nao encontrado para titulo {title!r}")

    body = without_title[: match.start()].strip()
    reflection = without_title[match.end() :].strip()
    return title, body, reflection


def import_workbook(path: Path) -> list[dict[str, str]]:
    frame = pd.read_excel(path, sheet_name=0, header=None)
    records: list[dict[str, str]] = []

    for index, row in frame.iterrows():
        if row.isna().all():
            continue

        month_day = parse_month_day(row.iloc[0])
        title, body, reflection = split_meditation(row.iloc[1])
        records.append(
            {
                "month_day": month_day,
                "title": title,
                "body": body,
                "reflection": reflection,
                "language": "pt-CV",
                "status": "published",
                "source": path.name,
            }
        )

    return sorted(records, key=lambda item: item["month_day"])


def write_outputs(records: list[dict[str, str]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "meditations.json"
    csv_path = output_dir / "meditations.csv"

    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa meditacoes SPH de uma planilha Excel.")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    records = import_workbook(args.workbook)
    write_outputs(records, args.output_dir)
    print(f"Imported {len(records)} meditations into {args.output_dir}")


if __name__ == "__main__":
    main()

