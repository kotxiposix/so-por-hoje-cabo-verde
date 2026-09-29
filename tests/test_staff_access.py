from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from sph.staff_access import (
    StaffAccessConfig,
    StaffAccessServiceError,
    StaffForbiddenError,
    SupabaseStaffAccess,
)


USER_ID = "7d40d2bb-6202-4e1f-9231-724d15fc8e02"
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


class StaffAccessTests(unittest.TestCase):
    def test_staff_access_requires_an_explicit_flag_and_private_values(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        }
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(StaffAccessServiceError):
                StaffAccessConfig.from_environment().validate()
        with patch.dict(os.environ, {**environment, "STAFF_ACCESS_READY": "true"}, clear=True):
            StaffAccessConfig.from_environment().validate()

    def test_moderator_access_uses_the_user_session_and_server_role_lookup(self) -> None:
        responses = [FakeResponse({"id": USER_ID}), FakeResponse([{"role": "moderator"}])]
        with patch("sph.staff_access.urlopen", side_effect=responses) as urlopen_mock:
            identity = SupabaseStaffAccess(config()).authorize(
                "Bearer user-access-token",
                {"moderator"},
            )

        self.assertEqual(identity.user_id, USER_ID)
        self.assertEqual(identity.roles, ("moderator",))
        user_request = urlopen_mock.call_args_list[0].args[0]
        role_request = urlopen_mock.call_args_list[1].args[0]
        self.assertEqual(user_request.headers["Authorization"], "Bearer user-access-token")
        self.assertEqual(role_request.headers["Authorization"], "Bearer service-role")
        self.assertIn("staff_roles", role_request.full_url)
        self.assertIn("status=eq.active", role_request.full_url)

    def test_admin_can_enter_each_staff_area(self) -> None:
        responses = [FakeResponse({"id": USER_ID}), FakeResponse([{"role": "admin"}])]
        with patch("sph.staff_access.urlopen", side_effect=responses):
            identity = SupabaseStaffAccess(config()).authorize(
                "Bearer user-access-token",
                {"help_editor"},
            )

        self.assertEqual(identity.roles, ("admin",))

    def test_opaque_secret_key_is_not_used_as_a_bearer_token(self) -> None:
        opaque_config = StaffAccessConfig(
            True,
            "https://project.supabase.co",
            "sb_secret_example",
        )
        responses = [FakeResponse({"id": USER_ID}), FakeResponse([{"role": "admin"}])]

        with patch("sph.staff_access.urlopen", side_effect=responses) as urlopen_mock:
            SupabaseStaffAccess(opaque_config).authorize(
                "Bearer user-access-token",
                {"admin"},
            )

        user_request = urlopen_mock.call_args_list[0].args[0]
        role_request = urlopen_mock.call_args_list[1].args[0]
        self.assertEqual(user_request.headers["Authorization"], "Bearer user-access-token")
        self.assertNotIn("Authorization", role_request.headers)

    def test_content_editor_is_a_valid_minimum_role(self) -> None:
        responses = [FakeResponse({"id": USER_ID}), FakeResponse([{"role": "content_editor"}])]
        with patch("sph.staff_access.urlopen", side_effect=responses):
            identity = SupabaseStaffAccess(config()).authorize(
                "Bearer user-access-token",
                {"content_editor"},
            )

        self.assertEqual(identity.roles, ("content_editor",))

    def test_wrong_or_suspended_role_is_forbidden(self) -> None:
        for records in ([{"role": "help_editor"}], []):
            responses = [FakeResponse({"id": USER_ID}), FakeResponse(records)]
            with patch("sph.staff_access.urlopen", side_effect=responses):
                with self.assertRaises(StaffForbiddenError):
                    SupabaseStaffAccess(config()).authorize(
                        "Bearer user-access-token",
                        {"moderator"},
                    )

    def test_browser_has_no_direct_staff_role_policy(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")

        self.assertIn("alter table public.staff_roles enable row level security", schema)
        self.assertIn('drop policy if exists "Users read staff roles"', schema)
        self.assertNotIn('create policy "Users read staff roles"', schema)


if __name__ == "__main__":
    unittest.main()
