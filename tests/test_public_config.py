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

    def test_push_requires_account_public_key_and_delivery_readiness(self) -> None:
        base = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_example",
            "VAPID_PUBLIC_KEY": "public-vapid-key",
        }
        self.assertFalse(public_runtime_config(base)["features"]["push"])

        config = public_runtime_config(
            {
                **base,
                "PUSH_DELIVERY_READY": "true",
                "VAPID_PRIVATE_KEY": "must-stay-private",
            }
        )

        self.assertTrue(config["features"]["push"])
        self.assertEqual(config["push"]["vapidPublicKey"], "public-vapid-key")
        self.assertNotIn("must-stay-private", repr(config))

    def test_ai_requires_account_private_keys_and_explicit_delivery_flag(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "OPENAI_API_KEY": "openai-secret",
        }

        self.assertFalse(public_runtime_config(environment)["features"]["ai"])

        environment["AI_DELIVERY_READY"] = "true"
        config = public_runtime_config(environment)

        self.assertTrue(config["features"]["ai"])
        self.assertNotIn("service-role", repr(config))
        self.assertNotIn("openai-secret", repr(config))


if __name__ == "__main__":
    unittest.main()
