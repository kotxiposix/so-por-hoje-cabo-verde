from __future__ import annotations

import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from sph.staff_access import StaffAccessConfig
from sph.staff_roles import (
    StaffRoleConflictError,
    StaffRoleInputError,
    SupabaseStaffRoles,
    normalize_email,
    public_staff_role,
)


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


def role_record() -> dict[str, str]:
    return {
        "user_id": TARGET_ID,
        "email": "Moderator@Example.cv",
        "role": "moderator",
        "status": "active",
        "updated_at": "2026-10-05T10:00:00+00:00",
    }


class StaffRoleTests(unittest.TestCase):
    def test_role_output_exposes_email_but_not_full_user_identifier(self) -> None:
        visible = public_staff_role(role_record())

        self.assertEqual(visible["email"], "moderator@example.cv")
        self.assertEqual(visible["user_ref"], "Conta …88dfee")
        self.assertNotIn("user_id", visible)
        self.assertNotIn(TARGET_ID, str(visible))

    def test_email_validation_is_exact_and_bounded(self) -> None:
        self.assertEqual(normalize_email("  TEAM@EXAMPLE.CV "), "team@example.cv")
        for value in ("", "sem-arroba", "a@b", "a b@example.cv", "a" * 255):
            with self.subTest(value=value), self.assertRaises(StaffRoleInputError):
                normalize_email(value)

    def test_list_uses_admin_rpc_and_private_service_key(self) -> None:
        with patch("sph.staff_roles.urlopen", return_value=FakeResponse([role_record()])) as request_mock:
            records = SupabaseStaffRoles(config()).list_roles(ACTOR_ID)

        request = request_mock.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/rest/v1/rpc/list_staff_roles"))
        self.assertEqual(request.headers["Authorization"], "Bearer service-role")
        self.assertEqual(json.loads(request.data), {"p_actor_id": ACTOR_ID})
        self.assertEqual(records[0]["role"], "moderator")

    def test_set_role_normalizes_input_and_uses_atomic_rpc(self) -> None:
        with patch("sph.staff_roles.urlopen", return_value=FakeResponse([role_record()])) as request_mock:
            visible = SupabaseStaffRoles(config()).set_role(
                ACTOR_ID,
                " Moderator@Example.cv ",
                "moderator",
                "active",
            )

        request = request_mock.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/rest/v1/rpc/manage_staff_role"))
        self.assertEqual(
            json.loads(request.data),
            {
                "p_actor_id": ACTOR_ID,
                "p_email": "moderator@example.cv",
                "p_role": "moderator",
                "p_status": "active",
            },
        )
        self.assertEqual(visible["status"], "active")

    def test_last_administrator_error_is_a_safe_conflict(self) -> None:
        error = HTTPError(
            "https://project.supabase.co/rest/v1/rpc/manage_staff_role",
            400,
            "Bad Request",
            None,
            io.BytesIO(json.dumps({"message": "Cannot suspend the last active administrator"}).encode()),
        )
        with patch("sph.staff_roles.urlopen", side_effect=error):
            with self.assertRaisesRegex(StaffRoleConflictError, "último administrador"):
                SupabaseStaffRoles(config()).set_role(
                    ACTOR_ID,
                    "admin@example.cv",
                    "admin",
                    "suspended",
                )

    def test_schema_keeps_role_management_private_atomic_and_audited(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")

        self.assertIn("create or replace function public.manage_staff_role", schema)
        self.assertIn("create or replace function public.list_staff_roles", schema)
        self.assertIn("for update;", schema)
        self.assertIn("Cannot suspend the last active administrator", schema)
        self.assertIn("staff_roles_audit_trigger", schema)
        self.assertIn("'staff_role.moderator.activated', 'staff_role.moderator.suspended'", schema)
        self.assertIn("grant execute on function public.manage_staff_role", schema)
        self.assertIn("to service_role;", schema)
        self.assertIn("from public, anon, authenticated;", schema)


if __name__ == "__main__":
    unittest.main()
