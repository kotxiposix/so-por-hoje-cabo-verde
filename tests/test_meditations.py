from __future__ import annotations

import json
import os
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from sph.repository import MeditationRepository
from sph.ai_support import (
    DailySupport,
    DailySupportRequest,
    build_daily_support,
    local_daily_support,
    validate_support_output,
)
from sph.service import DailyMeditationService


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "meditations.json"
SUPPORT_DATA_PATH = ROOT / "data" / "daily_support.json"
PUBLIC_DATA_PATH = ROOT / "public" / "data" / "meditations.json"
PUBLIC_SUPPORT_DATA_PATH = ROOT / "public" / "data" / "daily_support.json"


class MeditationTests(unittest.TestCase):
    def test_dataset_has_full_leap_year_coverage(self) -> None:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        keys = [record["month_day"] for record in records]

        self.assertEqual(len(records), 366)
        self.assertEqual(len(set(keys)), 366)
        self.assertIn("02-29", keys)
        self.assertIn("01-01", keys)
        self.assertIn("12-31", keys)

    def test_public_data_copies_match_the_canonical_files(self) -> None:
        self.assertEqual(DATA_PATH.read_bytes(), PUBLIC_DATA_PATH.read_bytes())
        self.assertEqual(SUPPORT_DATA_PATH.read_bytes(), PUBLIC_SUPPORT_DATA_PATH.read_bytes())

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
        meditation_days = {
            record["month_day"]
            for record in json.loads(DATA_PATH.read_text(encoding="utf-8"))
        }

        self.assertEqual(len(records), 366 * 4)
        self.assertEqual(len(pairs), 366 * 4)
        self.assertEqual({month_day for month_day, _ in pairs}, meditation_days)
        self.assertEqual(
            {state for month_day, state in pairs if month_day == "01-01"},
            {"standard", "ansioso", "risco", "consumo"},
        )

    def test_support_catalog_is_contextual_and_within_display_limits(self) -> None:
        records = json.loads(SUPPORT_DATA_PATH.read_text(encoding="utf-8"))
        meditations = {
            record["month_day"]: record
            for record in json.loads(DATA_PATH.read_text(encoding="utf-8"))
        }

        for record in records:
            with self.subTest(month_day=record["month_day"], state=record["state"]):
                title = meditations[record["month_day"]]["title"]
                self.assertIn(title, record["activity"])
                self.assertIn(title, record["mental_challenge"])
                self.assertLessEqual(len(record["activity"]), 420)
                self.assertLessEqual(len(record["phrase"]), 180)
                self.assertLessEqual(len(record["mental_challenge"]), 420)
                self.assertLessEqual(len(record["safety_note"]), 240)

        for state in ("standard", "ansioso", "risco", "consumo"):
            state_records = [record for record in records if record["state"] == state]
            self.assertGreaterEqual(len({record["activity"] for record in state_records}), 340)
            self.assertGreaterEqual(len({record["mental_challenge"] for record in state_records}), 340)

    def test_local_ai_support_uses_catalog(self) -> None:
        service = DailyMeditationService(MeditationRepository(DATA_PATH), "Atlantic/Cape_Verde")
        daily = service.for_date(date(2026, 1, 3))
        support = local_daily_support(DailySupportRequest(daily=daily, user_state="ansioso"))

        self.assertEqual(support.source, "catalog")
        self.assertTrue(support.activity)
        self.assertTrue(support.phrase)
        self.assertTrue(support.mental_challenge)

    def test_openai_is_not_used_without_explicit_server_authorization(self) -> None:
        service = DailyMeditationService(MeditationRepository(DATA_PATH), "Atlantic/Cape_Verde")
        request = DailySupportRequest(daily=service.for_date(date(2026, 1, 3)))

        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=False), patch(
            "sph.ai_support.openai_daily_support"
        ) as openai_support:
            support = build_daily_support(request)

        openai_support.assert_not_called()
        self.assertEqual(support.source, "catalog")

    def test_openai_can_be_used_after_server_authorization(self) -> None:
        service = DailyMeditationService(MeditationRepository(DATA_PATH), "Atlantic/Cape_Verde")
        request = DailySupportRequest(daily=service.for_date(date(2026, 1, 3)))
        expected = DailySupport(
            activity="Ação",
            phrase="Frase",
            mental_challenge="Desafio",
            safety_note="Nota",
            source="openai",
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=False), patch(
            "sph.ai_support.openai_daily_support", return_value=expected
        ) as openai_support:
            support = build_daily_support(request, allow_openai=True)

        openai_support.assert_called_once_with(request, "secret")
        self.assertEqual(support, expected)

    def test_openai_output_is_bounded_and_normalized(self) -> None:
        result = validate_support_output(
            {
                "activity": "  Liga a uma pessoa segura.  ",
                "phrase": "  Um dia de cada vez. ",
                "mental_challenge": "Escolhe pedir apoio antes de decidir.",
                "safety_note": "Não substitui ajuda profissional.",
            },
            "risco",
        )

        self.assertEqual(result["activity"], "Liga a uma pessoa segura.")
        with self.assertRaisesRegex(ValueError, "Campo de apoio inválido"):
            validate_support_output({**result, "activity": "a" * 421}, "standard")

    def test_high_risk_openai_output_requires_human_support(self) -> None:
        payload = {
            "activity": "Respira devagar durante um minuto.",
            "phrase": "Este momento vai passar.",
            "mental_challenge": "Observa o pensamento sem agir.",
            "safety_note": "Conteúdo complementar.",
        }

        with self.assertRaisesRegex(ValueError, "apoio humano"):
            validate_support_output(payload, "consumo")

        with self.assertRaisesRegex(ValueError, "apoio humano"):
            validate_support_output(
                {**payload, "safety_note": "Procura ajuda profissional."},
                "risco",
            )

    def test_openai_output_rejects_unsafe_medical_claims(self) -> None:
        payload = {
            "activity": "Pare de tomar a medicação e descansa.",
            "phrase": "Tudo ficará bem.",
            "mental_challenge": "Faz uma chamada de apoio.",
            "safety_note": "Conteúdo complementar.",
        }

        with self.assertRaisesRegex(ValueError, "orientação insegura"):
            validate_support_output(payload, "ansioso")


if __name__ == "__main__":
    unittest.main()
