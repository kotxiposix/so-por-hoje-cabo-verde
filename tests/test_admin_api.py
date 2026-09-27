from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from sph import api
from sph.security import admin_access_allowed
from sph.staff_access import (
    StaffAccessServiceError,
    StaffAuthenticationError,
    StaffForbiddenError,
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


if __name__ == "__main__":
    unittest.main()
