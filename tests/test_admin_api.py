from __future__ import annotations

import unittest

from sph.security import admin_access_allowed


class AdminApiTests(unittest.TestCase):
    def test_admin_endpoints_are_closed_when_secret_is_not_configured(self) -> None:
        self.assertFalse(admin_access_allowed("Bearer any-value", {}))

    def test_admin_endpoints_require_exact_bearer_secret(self) -> None:
        environment = {"ADMIN_API_SECRET": "expected-secret"}
        self.assertFalse(admin_access_allowed("Bearer wrong-secret", environment))
        self.assertFalse(admin_access_allowed(None, environment))
        self.assertTrue(admin_access_allowed("Bearer expected-secret", environment))


if __name__ == "__main__":
    unittest.main()
