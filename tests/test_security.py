from __future__ import annotations

import unittest

from sph.security import is_safe_https_origin, normalize_https_origin, supabase_headers


class HttpsOriginTests(unittest.TestCase):
    def test_normalizes_a_clean_https_origin(self) -> None:
        self.assertEqual(
            normalize_https_origin(" https://PROJECT.supabase.co/ "),
            "https://project.supabase.co",
        )
        self.assertTrue(is_safe_https_origin("https://project.supabase.co"))

    def test_rejects_origins_that_could_leak_credentials(self) -> None:
        for value in (
            "http://project.supabase.co",
            "https://user:secret@project.supabase.co",
            "https://project.supabase.co/rest/v1",
            "https://project.supabase.co?redirect=example.cv",
            "https://project.supabase.co/#fragment",
            "https://project.supabase.co\n.evil.example",
            "not-a-url",
            None,
        ):
            with self.subTest(value=value):
                self.assertEqual(normalize_https_origin(value), "")
                self.assertFalse(is_safe_https_origin(value))


class SupabaseHeaderTests(unittest.TestCase):
    def test_legacy_service_key_is_sent_as_bearer(self) -> None:
        headers = supabase_headers("legacy-service-role")

        self.assertEqual(headers["apikey"], "legacy-service-role")
        self.assertEqual(headers["Authorization"], "Bearer legacy-service-role")

    def test_opaque_secret_key_is_not_sent_as_jwt(self) -> None:
        headers = supabase_headers("sb_secret_example")

        self.assertEqual(headers["apikey"], "sb_secret_example")
        self.assertNotIn("Authorization", headers)

    def test_user_access_token_is_sent_with_opaque_project_key(self) -> None:
        headers = supabase_headers("sb_secret_example", authorization="user-access-token")

        self.assertEqual(headers["Authorization"], "Bearer user-access-token")


if __name__ == "__main__":
    unittest.main()
