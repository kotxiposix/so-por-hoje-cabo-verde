from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from sph.repository import MeditationRepository
from sph.ai_support import DailySupportRequest, local_daily_support
from sph.service import DailyMeditationService


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "meditations.json"
SUPPORT_DATA_PATH = ROOT / "data" / "daily_support.json"


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
        daily = service.for_date(date(2026, 1, 3))
        message = service.format_message(daily)

        self.assertIn("2026", message)
        self.assertNotIn("01-03", message)
        self.assertIn("SÓ POR HOJE:", message)
        self.assertIn(f"\n\n\n{daily.title}\n\n\n", message)
        self.assertIn("\n\n\nSÓ POR HOJE:\n\n", message)
        self.assertNotIn("\n\n\nSÓ POR HOJE:\n\n\n", message)
        self.assertIn("\n\n\nsoporhoje.cv\n\n\n", message)
        self.assertIn("Fonte oficial: Narcóticos Anónimos Portugal", message)
        self.assertIn(
            "Fonte oficial: Narcóticos Anónimos Portugal\n© NA World Services, Inc. Reprinted by permission.",
            message,
        )
        self.assertNotIn("https://na-pt.erlog.pt/sph.php", message)

    def test_local_ai_support_prioritizes_risk_state(self) -> None:
        service = DailyMeditationService(MeditationRepository(DATA_PATH), "Atlantic/Cape_Verde")
        daily = service.for_date(date(2026, 1, 3))
        support = local_daily_support(
            DailySupportRequest(
                daily=daily,
                user_state="risco",
                clean_days=12,
                reading_streak=3,
            )
        )

        combined = " ".join([support.activity, support.phrase, support.mental_challenge]).lower()
        self.assertIn("ajuda", combined)
        self.assertIn("segur", combined)
        self.assertIn("não substitui", support.safety_note.lower())

    def test_local_ai_support_is_complementary_not_official_literature(self) -> None:
        service = DailyMeditationService(MeditationRepository(DATA_PATH), "Atlantic/Cape_Verde")
        daily = service.for_date(date(2026, 1, 3))
        support = local_daily_support(DailySupportRequest(daily=daily))

        self.assertTrue(support.activity)
        self.assertTrue(support.phrase)
        self.assertTrue(support.mental_challenge)
        self.assertIn("não é literatura oficial", support.safety_note.lower())

    def test_support_catalog_has_four_states_per_day(self) -> None:
        records = json.loads(SUPPORT_DATA_PATH.read_text(encoding="utf-8"))
        pairs = {(record["month_day"], record["state"]) for record in records}

        self.assertEqual(len(records), 366 * 4)
        self.assertEqual(len(pairs), 366 * 4)
        self.assertEqual(
            {state for month_day, state in pairs if month_day == "01-01"},
            {"standard", "ansioso", "risco", "consumo"},
        )

    def test_local_ai_support_uses_catalog(self) -> None:
        service = DailyMeditationService(MeditationRepository(DATA_PATH), "Atlantic/Cape_Verde")
        daily = service.for_date(date(2026, 1, 3))
        support = local_daily_support(DailySupportRequest(daily=daily, user_state="ansioso"))

        self.assertEqual(support.source, "catalog")
        self.assertTrue(support.activity)
        self.assertTrue(support.phrase)
        self.assertTrue(support.mental_challenge)


if __name__ == "__main__":
    unittest.main()
