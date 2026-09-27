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
                "ACCOUNT_READY": "true",
                "SUPABASE_URL": "https://project.supabase.co/",
                "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_example",
                "SUPABASE_SERVICE_ROLE_KEY": "must-not-leak",
                "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
            }
        )

        self.assertTrue(config["features"]["account"])
        self.assertEqual(config["supabase"]["url"], "https://project.supabase.co")
        self.assertEqual(config["supabase"]["publishableKey"], "sb_publishable_example")
        self.assertEqual(config["turnstile"]["siteKey"], "1x00000000000000000000AA")
        self.assertNotIn("must-not-leak", repr(config))

    def test_account_stays_hidden_while_supabase_is_being_configured(self) -> None:
        config = public_runtime_config(
            {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_example",
            }
        )

        self.assertFalse(config["features"]["account"])
        self.assertNotIn("supabase", config)

    def test_account_stays_hidden_without_a_valid_turnstile_site_key(self) -> None:
        environment = {
            "ACCOUNT_READY": "true",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_example",
        }

        self.assertFalse(public_runtime_config(environment)["features"]["account"])
        environment["TURNSTILE_SITE_KEY"] = "bad site key"
        self.assertFalse(public_runtime_config(environment)["features"]["account"])

    def test_unsafe_supabase_origin_keeps_every_integration_closed(self) -> None:
        environment = {
            "ACCOUNT_READY": "true",
            "STAFF_ACCESS_READY": "true",
            "COMMUNITY_READY": "true",
            "HELP_DIRECTORY_READY": "true",
            "EDITORIAL_CONTENT_READY": "true",
            "SUPABASE_URL": "http://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
        }

        config = public_runtime_config(environment)

        self.assertFalse(any(config["features"].values()))
        self.assertNotIn("supabase", config)

    def test_staff_admin_is_separate_from_the_optional_public_account(self) -> None:
        environment = {
            "STAFF_ACCESS_READY": "true",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
        }

        config = public_runtime_config(environment)

        self.assertFalse(config["features"]["account"])
        self.assertTrue(config["features"]["staffAdmin"])
        self.assertIn("supabase", config)
        self.assertNotIn("service-role", repr(config))

    def test_push_requires_account_public_key_and_delivery_readiness(self) -> None:
        base = {
            "ACCOUNT_READY": "true",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_example",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
            "VAPID_PUBLIC_KEY": "public-vapid-key",
            "VAPID_PRIVATE_KEY": "private-vapid-key",
            "VAPID_SUBJECT": "mailto:team@example.cv",
            "PUSH_CRON_SECRET": "cron-secret",
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

    def test_push_stays_hidden_when_any_delivery_secret_is_missing(self) -> None:
        environment = {
            "ACCOUNT_READY": "true",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
            "PUSH_DELIVERY_READY": "true",
            "VAPID_PUBLIC_KEY": "public-vapid-key",
            "VAPID_PRIVATE_KEY": "private-vapid-key",
            "VAPID_SUBJECT": "mailto:team@example.cv",
        }

        self.assertFalse(public_runtime_config(environment)["features"]["push"])

        environment["PUSH_CRON_SECRET"] = "cron-secret"
        self.assertTrue(public_runtime_config(environment)["features"]["push"])

    def test_ai_requires_account_private_keys_and_explicit_delivery_flag(self) -> None:
        environment = {
            "ACCOUNT_READY": "true",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
            "OPENAI_API_KEY": "openai-secret",
        }

        self.assertFalse(public_runtime_config(environment)["features"]["ai"])

        environment["AI_DELIVERY_READY"] = "true"
        config = public_runtime_config(environment)

        self.assertTrue(config["features"]["ai"])
        self.assertNotIn("service-role", repr(config))
        self.assertNotIn("openai-secret", repr(config))

    def test_community_requires_account_service_role_and_explicit_readiness(self) -> None:
        environment = {
            "ACCOUNT_READY": "true",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
        }

        self.assertFalse(public_runtime_config(environment)["features"]["community"])

        environment["COMMUNITY_READY"] = "true"
        self.assertFalse(public_runtime_config(environment)["features"]["community"])

        environment["STAFF_ACCESS_READY"] = "true"
        config = public_runtime_config(environment)

        self.assertTrue(config["features"]["community"])
        self.assertNotIn("service-role", repr(config))

    def test_help_directory_requires_service_role_and_explicit_readiness(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
        }

        self.assertFalse(public_runtime_config(environment)["features"]["helpDirectory"])

        environment["HELP_DIRECTORY_READY"] = "true"
        self.assertFalse(public_runtime_config(environment)["features"]["helpDirectory"])

        environment["STAFF_ACCESS_READY"] = "true"
        config = public_runtime_config(environment)

        self.assertTrue(config["features"]["helpDirectory"])
        self.assertNotIn("service-role", repr(config))

    def test_editorial_content_requires_staff_service_role_and_explicit_readiness(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
        }

        self.assertFalse(public_runtime_config(environment)["features"]["editorialContent"])
        environment["EDITORIAL_CONTENT_READY"] = "true"
        self.assertFalse(public_runtime_config(environment)["features"]["editorialContent"])
        environment["STAFF_ACCESS_READY"] = "true"

        config = public_runtime_config(environment)

        self.assertTrue(config["features"]["editorialContent"])
        self.assertNotIn("service-role", repr(config))


if __name__ == "__main__":
    unittest.main()
