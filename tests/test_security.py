from __future__ import annotations

import unittest

from sph.security import is_safe_https_origin, normalize_https_origin


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


if __name__ == "__main__":
    unittest.main()
