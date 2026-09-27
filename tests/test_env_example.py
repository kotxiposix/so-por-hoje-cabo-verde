from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / ".env.example"
GITIGNORE_PATH = ROOT / ".gitignore"


def parse_environment_example() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in EXAMPLE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if not separator:
            raise AssertionError(f"Linha de ambiente inválida: {raw_line}")
        values[name] = value
    return values


class EnvironmentExampleTests(unittest.TestCase):
    def test_sensitive_values_are_empty_and_feature_flags_are_closed(self) -> None:
        values = parse_environment_example()
        sensitive = {
            "SUPABASE_URL",
            "SUPABASE_PUBLISHABLE_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "ADMIN_API_SECRET",
            "OPENAI_API_KEY",
            "VAPID_PUBLIC_KEY",
            "VAPID_PRIVATE_KEY",
            "VAPID_SUBJECT",
            "PUSH_CRON_SECRET",
        }
        feature_flags = {
            "ACCOUNT_READY",
            "STAFF_ACCESS_READY",
            "AI_DELIVERY_READY",
            "PUSH_DELIVERY_READY",
            "COMMUNITY_READY",
            "HELP_DIRECTORY_READY",
            "EDITORIAL_CONTENT_READY",
        }

        self.assertTrue(sensitive.issubset(values))
        self.assertTrue(all(values[name] == "" for name in sensitive))
        self.assertTrue(feature_flags.issubset(values))
        self.assertTrue(all(values[name] == "false" for name in feature_flags))

    def test_local_environment_files_are_ignored_but_example_is_tracked(self) -> None:
        patterns = set(GITIGNORE_PATH.read_text(encoding="utf-8").splitlines())

        self.assertIn(".env", patterns)
        self.assertIn(".env.*", patterns)
        self.assertIn("!.env.example", patterns)


if __name__ == "__main__":
    unittest.main()
