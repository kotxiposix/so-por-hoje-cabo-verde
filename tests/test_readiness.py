from __future__ import annotations

import unittest

from scripts.check_readiness import readiness_report


class ReadinessTests(unittest.TestCase):
    def test_empty_environment_keeps_every_integration_closed(self) -> None:
        report = readiness_report({})

        self.assertTrue(all(not item["public"] for item in report.values()))
        self.assertIn("SUPABASE_URL", report["account"]["missing"])
        self.assertIn("SUPABASE_URL", report["staffAdmin"]["missing"])
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
        environment = {
            "ACCOUNT_READY": "true",
            "SUPABASE_URL": "https://secret-project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "public-but-not-for-report",
            "SUPABASE_SERVICE_ROLE_KEY": "service-secret",
            "ADMIN_API_SECRET": "admin-secret",
            "STAFF_ACCESS_READY": "true",
            "AI_DELIVERY_READY": "true",
            "OPENAI_API_KEY": "openai-secret",
            "OPENAI_MODEL": "configured-model",
            "AI_DAILY_LIMIT": "3",
            "PUSH_DELIVERY_READY": "true",
            "VAPID_PUBLIC_KEY": "vapid-public",
            "VAPID_PRIVATE_KEY": "vapid-private",
            "VAPID_SUBJECT": "mailto:team@example.cv",
            "PUSH_CRON_SECRET": "cron-secret",
            "COMMUNITY_READY": "true",
            "HELP_DIRECTORY_READY": "true",
            "EDITORIAL_CONTENT_READY": "true",
        }

        report = readiness_report(environment)

        self.assertTrue(all(item["public"] for item in report.values()))
        self.assertTrue(all(not item["missing"] for item in report.values()))
        rendered = repr(report)
        for secret in ("service-secret", "admin-secret", "openai-secret", "vapid-private", "cron-secret"):
            self.assertNotIn(secret, rendered)


if __name__ == "__main__":
    unittest.main()
