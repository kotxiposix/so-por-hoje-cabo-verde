from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from sph.staff_access import StaffAccessConfig
from sph.staff_audit import SupabaseStaffAudit, public_audit_event


ACTOR_ID = "7d40d2bb-6202-4e1f-9231-724d15fc8e02"
TARGET_ID = "4948b21e-facf-4bc8-a60e-8800b488dfee"
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


def config() -> StaffAccessConfig:
    return StaffAccessConfig(True, "https://project.supabase.co", "service-role")


def event() -> dict[str, object]:
    return {
        "actor_id": ACTOR_ID,
        "action": "help.verified",
        "target_type": "help_resource",
        "target_id": TARGET_ID,
        "created_at": "2026-09-27T10:00:00+00:00",
        "private_note": "never expose",
    }


class StaffAuditTests(unittest.TestCase):
    def test_public_event_uses_short_references_and_minimum_fields(self) -> None:
        visible = public_audit_event(event())

        self.assertEqual(
            set(visible),
            {"action", "target_type", "target_ref", "actor_ref", "created_at"},
        )
        self.assertNotIn(ACTOR_ID, str(visible))
        self.assertNotIn(TARGET_ID, str(visible))
        self.assertNotIn("never expose", str(visible))

    def test_service_uses_role_key_and_bounds_the_query(self) -> None:
        with patch("sph.staff_audit.urlopen", return_value=FakeResponse([event()])) as request_mock:
            visible = SupabaseStaffAudit(config()).list_events(999)

        request = request_mock.call_args.args[0]
        self.assertIn("limit=200", request.full_url)
        self.assertEqual(request.headers["Authorization"], "Bearer service-role")
        self.assertEqual(len(visible), 1)

    def test_schema_audit_is_atomic_private_and_content_free(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        table = schema.split("create table if not exists public.staff_audit_events", 1)[1].split(");", 1)[0]

        self.assertIn("actor_id uuid", table)
        self.assertIn("target_id uuid", table)
        self.assertNotIn("body", table)
        self.assertNotIn("note", table)
        self.assertNotIn("phone", table)
        self.assertIn("after update of status on public.anonymous_posts", schema)
        self.assertIn("after insert or update on public.help_resources", schema)
        self.assertIn("after insert or update on public.editorial_content", schema)
        self.assertIn("revoke all on function public.audit_community_moderation()", schema)
        self.assertIn("revoke all on function public.audit_help_resource_change()", schema)
        self.assertIn("revoke all on function public.audit_editorial_content_change()", schema)
        self.assertIn("alter table public.staff_audit_events enable row level security", schema)
        self.assertIn('drop policy if exists "Users read staff audit events"', schema)
        self.assertNotIn('create policy "Users read staff audit events"', schema)


if __name__ == "__main__":
    unittest.main()
