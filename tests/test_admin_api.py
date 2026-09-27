from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from sph import api
from sph.security import admin_access_allowed
from sph.send_log import SendLogEntry
from sph.staff_access import (
    StaffAccessServiceError,
    StaffAuthenticationError,
    StaffForbiddenError,
    StaffIdentity,
)


class AdminApiTests(unittest.TestCase):
    def test_admin_endpoints_are_closed_when_secret_is_not_configured(self) -> None:
        self.assertFalse(admin_access_allowed("Bearer any-value", {}))

    def test_admin_endpoints_require_exact_bearer_secret(self) -> None:
        environment = {"ADMIN_API_SECRET": "expected-secret"}
        self.assertFalse(admin_access_allowed("Bearer wrong-secret", environment))
        self.assertFalse(admin_access_allowed(None, environment))
        self.assertTrue(admin_access_allowed("Bearer expected-secret", environment))

    def test_staff_access_maps_authentication_permission_and_service_failures(self) -> None:
        cases = (
            (StaffAuthenticationError("sessão"), 401),
            (StaffForbiddenError("papel"), 403),
            (StaffAccessServiceError("serviço"), 503),
        )
        for error, expected_status in cases:
            with self.subTest(status=expected_status), patch(
                "sph.api.SupabaseStaffAccess"
            ) as access_class:
                access_class.return_value.authorize.side_effect = error
                with self.assertRaises(HTTPException) as raised:
                    api.require_staff_access("Bearer token", {"moderator"})
                self.assertEqual(raised.exception.status_code, expected_status)

    def test_editorial_routes_request_the_minimum_staff_role(self) -> None:
        with patch("sph.api.require_staff_access") as require_access, patch(
            "sph.api.community_service"
        ) as community_service:
            community_service.return_value.list_pending_posts.return_value = []
            api.pending_community_posts(limit=10, authorization="Bearer token")
            require_access.assert_called_once_with("Bearer token", {"moderator"})

        with patch("sph.api.require_staff_access") as require_access, patch(
            "sph.api.help_directory_service"
        ) as help_service:
            help_service.return_value.list_for_review.return_value = []
            api.help_resources_for_review(limit=10, authorization="Bearer token")
            require_access.assert_called_once_with("Bearer token", {"help_editor"})

    def test_staff_profile_exposes_roles_without_user_identity(self) -> None:
        identity = StaffIdentity(
            user_id="7d40d2bb-6202-4e1f-9231-724d15fc8e02",
            roles=("help_editor",),
        )
        with patch("sph.api.require_staff_access", return_value=identity):
            result = api.staff_profile("Bearer token")

        self.assertEqual(result, {"roles": ["help_editor"]})
        self.assertNotIn("user_id", result)

    def test_staff_delivery_logs_require_admin_and_hide_sensitive_fields(self) -> None:
        entry = SendLogEntry(
            send_date="2026-09-27",
            month_day="09-27",
            channel="messenger",
            destination_id="private-destination",
            status="failed",
            message_hash="private-message-hash",
            error_message="provider detail",
            sent_at="2026-09-27T08:00:00-01:00",
        )
        with patch("sph.api.require_staff_access") as require_access, patch.object(
            api.send_log, "list", return_value=[entry]
        ):
            result = api.staff_send_logs(limit=10, authorization="Bearer token")

        require_access.assert_called_once_with("Bearer token", {"admin"})
        self.assertEqual(result["summary"], {"total": 1, "sent": 0, "failed": 1})
        self.assertEqual(
            set(result["entries"][0]),
            {"send_date", "month_day", "channel", "status", "sent_at"},
        )
        self.assertNotIn("private-destination", str(result))
        self.assertNotIn("provider detail", str(result))

    def test_staff_audit_route_requires_admin(self) -> None:
        with patch("sph.api.require_staff_access") as require_access, patch(
            "sph.api.staff_audit_service"
        ) as audit_service:
            audit_service.return_value.list_events.return_value = []
            result = api.staff_audit_events(limit=25, authorization="Bearer token")

        self.assertEqual(result, [])
        require_access.assert_called_once_with("Bearer token", {"admin"})
        audit_service.return_value.list_events.assert_called_once_with(25)

    def test_editorial_mutations_attach_the_authenticated_staff_identity(self) -> None:
        identity = StaffIdentity(
            user_id="7d40d2bb-6202-4e1f-9231-724d15fc8e02",
            roles=("admin",),
        )
        with patch("sph.api.require_staff_access", return_value=identity), patch(
            "sph.api.community_service"
        ) as community_service:
            api.moderate_community_post(
                "7a0c9820-4e7a-40f6-a32b-6f5ce402ef68",
                api.CommunityModerationPayload(status="rejected", note=None),
                authorization="Bearer token",
            )
            community_service.return_value.moderate_post.assert_called_once_with(
                "7a0c9820-4e7a-40f6-a32b-6f5ce402ef68",
                "rejected",
                None,
                actor_id=identity.user_id,
            )

        resource_payload = api.HelpResourcePayload(name="Recurso", category="information")
        with patch("sph.api.require_staff_access", return_value=identity), patch(
            "sph.api.help_directory_service"
        ) as help_service:
            api.create_help_resource(resource_payload, authorization="Bearer token")
            help_service.return_value.create_draft.assert_called_once_with(
                resource_payload.model_dump(),
                actor_id=identity.user_id,
            )


if __name__ == "__main__":
    unittest.main()
