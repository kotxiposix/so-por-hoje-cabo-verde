from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from sph.help_directory import (
    HelpDirectoryConfig,
    HelpDirectoryInputError,
    HelpDirectoryServiceError,
    SupabaseHelpDirectory,
    normalize_resource,
    public_resource,
    validate_verifiable_resource,
)


RESOURCE_ID = "4948b21e-facf-4bc8-a60e-8800b488dfee"
EDITOR_ID = "7d40d2bb-6202-4e1f-9231-724d15fc8e02"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "supabase" / "schema.sql"


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def config() -> HelpDirectoryConfig:
    return HelpDirectoryConfig(True, "https://project.supabase.co", "service-role")


def payload() -> dict[str, object]:
    return {
        "name": "Linha de apoio",
        "island": "Santiago",
        "municipality": "Praia",
        "category": "emergency",
        "description": "Atendimento confirmado pela fonte responsável.",
        "phone": "+238 000 00 00",
        "email": "apoio@example.cv",
        "website": "https://example.cv/apoio",
        "schedule": ["Todos os dias · 24 horas"],
        "is_emergency": True,
        "source_url": "https://example.cv/fonte",
    }


class HelpDirectoryTests(unittest.TestCase):
    def test_directory_is_closed_until_explicitly_enabled(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        }
        with patch.dict(os.environ, environment, clear=True):
            config_value = HelpDirectoryConfig.from_environment()
            self.assertTrue(config_value.management_ready)
            self.assertFalse(config_value.ready)
        with patch.dict(os.environ, {**environment, "HELP_DIRECTORY_READY": "true"}, clear=True):
            self.assertTrue(HelpDirectoryConfig.from_environment().ready)

    def test_drafts_can_be_managed_without_opening_the_public_directory(self) -> None:
        management_config = HelpDirectoryConfig(False, "https://project.supabase.co", "service-role")
        directory = SupabaseHelpDirectory(management_config)

        with self.assertRaises(HelpDirectoryServiceError):
            directory.list_verified()

        returned = [payload() | {"id": RESOURCE_ID, "verification_status": "draft"}]
        with patch("sph.help_directory.urlopen", return_value=FakeResponse(returned)):
            created = directory.create_draft(payload())

        self.assertEqual(created["verification_status"], "draft")

    def test_resource_validation_rejects_untrusted_urls_and_categories(self) -> None:
        unsafe = payload() | {"website": "javascript:alert(1)"}
        with self.assertRaises(HelpDirectoryInputError):
            normalize_resource(unsafe)
        with self.assertRaises(HelpDirectoryInputError):
            normalize_resource(payload() | {"website": "http://example.cv"})
        with self.assertRaises(HelpDirectoryInputError):
            normalize_resource(payload() | {"category": "unknown"})
        with self.assertRaises(HelpDirectoryInputError):
            normalize_resource(payload() | {"email": "not-an-email"})
        with self.assertRaises(HelpDirectoryInputError):
            normalize_resource(payload() | {"phone": "123"})
        with self.assertRaises(HelpDirectoryInputError):
            normalize_resource(payload() | {"is_emergency": "false"})

    def test_public_shape_excludes_internal_review_fields(self) -> None:
        record = payload() | {
            "id": RESOURCE_ID,
            "is_verified": True,
            "verification_status": "verified",
            "moderation_note": "internal",
            "review_due_at": "2026-12-01",
        }

        visible = public_resource(record)

        self.assertEqual(visible["id"], RESOURCE_ID)
        self.assertNotIn("is_verified", visible)
        self.assertNotIn("verification_status", visible)
        self.assertNotIn("moderation_note", visible)

    def test_public_listing_requires_valid_verification_date(self) -> None:
        returned = [payload() | {
            "id": RESOURCE_ID,
            "verified_at": "2026-09-01T10:00:00+00:00",
            "review_due_at": "2026-12-01",
        }]
        with patch("sph.help_directory.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            result = SupabaseHelpDirectory(config()).list_verified(999)

        request = urlopen_mock.call_args.args[0]
        self.assertIn("is_verified=eq.true", request.full_url)
        self.assertIn("verification_status=eq.verified", request.full_url)
        self.assertIn("review_due_at=gte.", request.full_url)
        self.assertIn("limit=200", request.full_url)
        self.assertNotIn("select=*", request.full_url)
        self.assertEqual(result[0]["id"], RESOURCE_ID)

    def test_public_listing_skips_an_unsafe_database_record(self) -> None:
        unsafe = payload() | {
            "id": RESOURCE_ID,
            "website": "javascript:alert(1)",
            "review_due_at": "2026-12-01",
        }
        safe = payload() | {
            "id": "e00acccc-0f83-4132-8949-cd090a217c20",
            "review_due_at": "2026-12-01",
        }
        with patch("sph.help_directory.urlopen", return_value=FakeResponse([unsafe, safe])):
            result = SupabaseHelpDirectory(config()).list_verified()

        self.assertEqual([item["id"] for item in result], [safe["id"]])

    def test_public_listing_reports_directory_unavailability(self) -> None:
        with patch("sph.help_directory.urlopen", side_effect=OSError("offline")):
            with self.assertRaisesRegex(
                HelpDirectoryServiceError,
                "Não foi possível contactar o diretório",
            ):
                SupabaseHelpDirectory(config()).list_verified()

    def test_create_and_update_always_return_resource_to_draft(self) -> None:
        returned = [payload() | {"id": RESOURCE_ID, "verification_status": "draft"}]
        with patch("sph.help_directory.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            SupabaseHelpDirectory(config()).create_draft(payload(), actor_id=EDITOR_ID)

        request_payload = json.loads(urlopen_mock.call_args.args[0].data)
        self.assertFalse(request_payload["is_verified"])
        self.assertEqual(request_payload["verification_status"], "draft")
        self.assertIsNone(request_payload["verified_at"])
        self.assertIsNone(request_payload["review_due_at"])
        self.assertEqual(request_payload["last_edited_by"], EDITOR_ID)

    def test_verification_requires_a_source_and_sets_review_deadline(self) -> None:
        returned = [payload() | {"id": RESOURCE_ID, "verification_status": "verified"}]
        with patch("sph.help_directory.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            SupabaseHelpDirectory(config()).verify(RESOURCE_ID, 90, actor_id=EDITOR_ID)

        request = urlopen_mock.call_args.args[0]
        request_payload = json.loads(request.data)
        self.assertEqual(urlopen_mock.call_count, 2)
        self.assertIn(f"id=eq.{RESOURCE_ID}", request.full_url)
        self.assertTrue(request_payload["is_verified"])
        self.assertEqual(request_payload["verification_status"], "verified")
        self.assertEqual(request_payload["last_edited_by"], EDITOR_ID)
        self.assertRegex(request_payload["review_due_at"], r"^\d{4}-\d{2}-\d{2}$")

    def test_verification_requires_actionable_emergency_and_meeting_details(self) -> None:
        with self.assertRaisesRegex(HelpDirectoryInputError, "telefone confirmado"):
            validate_verifiable_resource(payload() | {"phone": None})

        meeting = payload() | {
            "category": "meeting",
            "is_emergency": False,
            "schedule": [],
        }
        with self.assertRaisesRegex(HelpDirectoryInputError, "horário confirmado"):
            validate_verifiable_resource(meeting)

        with self.assertRaisesRegex(HelpDirectoryInputError, "contacto confirmado"):
            validate_verifiable_resource(meeting | {
                "schedule": ["Terça · 18h"],
                "phone": None,
                "email": None,
                "website": None,
            })

    def test_retirement_removes_public_eligibility_without_deleting_history(self) -> None:
        returned = [payload() | {
            "id": RESOURCE_ID,
            "is_verified": False,
            "verification_status": "retired",
            "review_due_at": None,
        }]
        with patch("sph.help_directory.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            retired = SupabaseHelpDirectory(config()).retire(RESOURCE_ID, actor_id=EDITOR_ID)

        request = urlopen_mock.call_args.args[0]
        request_payload = json.loads(request.data)
        self.assertEqual(request.method, "PATCH")
        self.assertIn(f"id=eq.{RESOURCE_ID}", request.full_url)
        self.assertFalse(request_payload["is_verified"])
        self.assertEqual(request_payload["verification_status"], "retired")
        self.assertIsNone(request_payload["review_due_at"])
        self.assertEqual(request_payload["last_edited_by"], EDITOR_ID)
        self.assertEqual(retired["id"], RESOURCE_ID)

    def test_browser_has_no_direct_help_directory_policy(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")

        self.assertIn('drop policy if exists "Public reads verified help resources"', schema)
        self.assertNotIn('create policy "Public reads verified help resources"', schema)
        self.assertIn("review_due_at date", schema)
        self.assertIn("last_edited_by uuid references auth.users(id) on delete set null", schema)
        self.assertIn("create trigger help_resources_audit_trigger", schema)


if __name__ == "__main__":
    unittest.main()
