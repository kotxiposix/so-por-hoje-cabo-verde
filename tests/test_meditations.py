from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from sph.repository import MeditationRepository
from sph.service import DailyMeditationService


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "meditations.json"


class MeditationTests(unittest.TestCase):
    def test_dataset_has_full_leap_year_coverage(self) -> None:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        keys = [record["month_day"] for record in records]

        self.assertEqual(len(records), 366)
        self.assertEqual(len(set(keys)), 366)
        self.assertIn("02-29", keys)
        self.assertIn("01-01", keys)
        self.assertIn("12-31", keys)

    def test_daily_service_uses_month_day_without_year(self) -> None:
        service = DailyMeditationService(MeditationRepository(DATA_PATH), "Atlantic/Cape_Verde")
        daily = service.for_date(date(2026, 1, 3))

        self.assertEqual(daily.date, "2026-01-03")
        self.assertEqual(daily.month_day, "01-03")
        self.assertTrue(daily.title)
        self.assertTrue(daily.reflection)

    def test_preview_message_contains_generated_year(self) -> None:
        service = DailyMeditationService(MeditationRepository(DATA_PATH), "Atlantic/Cape_Verde")
        message = service.format_message(service.for_date(date(2026, 1, 3)))

        self.assertIn("2026", message)
        self.assertNotIn("01-03", message)
        self.assertIn("SÓ POR HOJE:", message)
        self.assertIn("Fonte oficial: Narcóticos Anónimos Portugal", message)


if __name__ == "__main__":
    unittest.main()
