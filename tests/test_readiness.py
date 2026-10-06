from __future__ import annotations

import base64
import unittest

from scripts.check_readiness import readiness_report


class ReadinessTests(unittest.TestCase):
    def test_empty_environment_keeps_every_integration_closed(self) -> None:
        report = readiness_report({})

        self.assertTrue(all(not item["public"] for item in report.values()))
        self.assertIn("SUPABASE_URL", report["account"]["missing"])
        self.assertIn("SUPABASE_URL", report["staffAdmin"]["missing"])
        self.assertIn("TURNSTILE_SITE_KEY", report["account"]["missing"])
        self.assertIn("OPENAI_API_KEY", report["ai"]["missing"])
        self.assertIn("VAPID_PRIVATE_KEY", report["push"]["missing"])
        self.assertEqual(report["ai"]["disabledDependencies"], ["ACCOUNT_READY"])
        self.assertEqual(
            report["community"]["disabledDependencies"],
            ["ACCOUNT_READY", "STAFF_ACCESS_READY"],
        )
        self.assertFalse(report["helpDirectory"]["dependenciesReady"])

    def test_false_dependency_flag_is_not_treated_as_ready(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-secret",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
            "STAFF_ACCESS_READY": "false",
            "HELP_DIRECTORY_READY": "true",
            "EDITORIAL_CONTENT_READY": "true",
        }

        report = readiness_report(environment)

        self.assertFalse(report["helpDirectory"]["configured"])
        self.assertFalse(report["helpDirectory"]["public"])
        self.assertEqual(
            report["helpDirectory"]["disabledDependencies"],
            ["STAFF_ACCESS_READY"],
        )
        self.assertFalse(report["editorialContent"]["configured"])

    def test_complete_environment_reports_active_features_without_values(self) -> None:
        vapid_public_key = base64.urlsafe_b64encode(b"\x04" + (b"\x00" * 64)).decode().rstrip("=")
        vapid_private_key = (
            "-----BEGIN PRIVATE KEY-----\n"
            + ("A" * 128)
            + "\n-----END PRIVATE KEY-----"
        )
        environment = {
            "ACCOUNT_READY": "true",
            "SUPABASE_URL": "https://secret-project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-but-not-for-report",
            "SUPABASE_SERVICE_ROLE_KEY": "service-secret",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
            "ADMIN_API_SECRET": "admin-secret",
            "STAFF_ACCESS_READY": "true",
            "AI_DELIVERY_READY": "true",
            "OPENAI_API_KEY": "openai-secret",
            "OPENAI_MODEL": "configured-model",
            "AI_DAILY_LIMIT": "3",
            "PUSH_DELIVERY_READY": "true",
            "VAPID_PUBLIC_KEY": vapid_public_key,
            "VAPID_PRIVATE_KEY": vapid_private_key,
            "VAPID_SUBJECT": "mailto:team@example.cv",
            "PUSH_CRON_SECRET": "c" * 48,
            "COMMUNITY_READY": "true",
            "HELP_DIRECTORY_READY": "true",
            "EDITORIAL_CONTENT_READY": "true",
        }

        report = readiness_report(environment)

        self.assertTrue(all(item["public"] for item in report.values()))
        self.assertTrue(all(not item["missing"] for item in report.values()))
        self.assertTrue(all(not item["invalid"] for item in report.values()))
        rendered = repr(report)
        for secret in ("service-secret", "admin-secret", "openai-secret", vapid_private_key, "c" * 48):
            self.assertNotIn(secret, rendered)

    def test_invalid_push_and_ai_values_are_reported_by_name_only(self) -> None:
        environment = {
            "ACCOUNT_READY": "true",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-secret",
            "TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
            "AI_DELIVERY_READY": "false",
            "OPENAI_API_KEY": "openai-secret",
            "OPENAI_MODEL": "model with spaces",
            "AI_DAILY_LIMIT": "0",
            "PUSH_DELIVERY_READY": "false",
            "VAPID_PUBLIC_KEY": "not-a-key",
            "VAPID_PRIVATE_KEY": "not-a-private-key",
            "VAPID_SUBJECT": "team@example.cv",
            "PUSH_CRON_SECRET": "short",
        }

        report = readiness_report(environment)

        self.assertFalse(report["ai"]["configured"])
        self.assertEqual(report["ai"]["invalid"], ["OPENAI_MODEL", "AI_DAILY_LIMIT"])
        self.assertFalse(report["push"]["configured"])
        self.assertEqual(
            report["push"]["invalid"],
            ["VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY", "VAPID_SUBJECT", "PUSH_CRON_SECRET"],
        )
        rendered = repr(report)
        self.assertNotIn("model with spaces", rendered)
        self.assertNotIn("not-a-private-key", rendered)


if __name__ == "__main__":
    unittest.main()
