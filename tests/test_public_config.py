from __future__ import annotations

import unittest

from sph.public_config import public_runtime_config


class PublicConfigTests(unittest.TestCase):
    def test_account_is_disabled_without_public_supabase_values(self) -> None:
        config = public_runtime_config({})

        self.assertFalse(config["features"]["account"])
        self.assertNotIn("supabase", config)

    def test_only_public_supabase_values_are_exposed(self) -> None:
        config = public_runtime_config(
            {
                "SUPABASE_URL": "https://project.supabase.co/",
                "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_example",
                "SUPABASE_SERVICE_ROLE_KEY": "must-not-leak",
            }
        )

        self.assertTrue(config["features"]["account"])
        self.assertEqual(config["supabase"]["url"], "https://project.supabase.co")
        self.assertEqual(config["supabase"]["publishableKey"], "sb_publishable_example")
        self.assertNotIn("must-not-leak", repr(config))


if __name__ == "__main__":
    unittest.main()
