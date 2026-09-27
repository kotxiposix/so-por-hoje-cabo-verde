from __future__ import annotations

import re
import unittest
from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "supabase" / "schema.sql"


class JourneySyncSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = SCHEMA_PATH.read_text(encoding="utf-8")

    def test_atomic_save_uses_authenticated_identity_and_conflict_timestamp(self) -> None:
        function = re.search(
            r"create or replace function public\.save_journey_state\((.*?)\n\$\$;",
            self.schema,
            re.S,
        )
        self.assertIsNotNone(function)
        body = function.group(0)

        self.assertIn("security invoker", body)
        self.assertIn("auth.uid()", body)
        self.assertIn("for update", body)
        self.assertIn("stored_updated_at <> p_expected_updated_at", body)
        self.assertIn("return query select false, stored_updated_at", body)

    def test_atomic_save_is_not_executable_by_anonymous_visitors(self) -> None:
        signature = "public.save_journey_state(jsonb, integer, timestamptz, boolean)"
        self.assertIn(f"revoke all on function {signature}\n  from public, anon;", self.schema)
        self.assertIn(f"grant execute on function {signature}\n  to authenticated;", self.schema)

    def test_push_delivery_claim_is_atomic_and_service_role_only(self) -> None:
        self.assertIn("create or replace function public.claim_push_delivery", self.schema)
        self.assertIn("delivery_claimed_at < p_claimed_at - interval '5 minutes'", self.schema)
        self.assertIn("last_sent_on is distinct from p_local_day", self.schema)
        for function_name in ("claim", "complete", "release"):
            signature = f"public.{function_name}_push_delivery(uuid, date, timestamptz)"
            self.assertIn(
                f"revoke all on function {signature}\n  from public, anon, authenticated;",
                self.schema,
            )
            self.assertIn(f"grant execute on function {signature}\n  to service_role;", self.schema)

    def test_push_subscriptions_reject_unsafe_endpoints_and_key_material(self) -> None:
        self.assertIn("push_subscriptions_endpoint_safe", self.schema)
        self.assertIn("endpoint ~ '^https://[^[:space:]@/]+'", self.schema)
        self.assertIn("lower(endpoint) !~ '^https://(localhost", self.schema)
        self.assertIn("push_subscriptions_key_material_safe", self.schema)
        self.assertIn("p256dh ~ '^[A-Za-z0-9_-]+={0,2}$'", self.schema)
        self.assertIn("auth_secret ~ '^[A-Za-z0-9_-]+={0,2}$'", self.schema)

    def test_every_public_table_enables_row_level_security(self) -> None:
        tables = set(re.findall(
            r"create table if not exists public\.([a-z_]+)\s*\(",
            self.schema,
        ))
        rls_tables = set(re.findall(
            r"alter table public\.([a-z_]+) enable row level security;",
            self.schema,
        ))

        self.assertTrue(tables)
        self.assertEqual(rls_tables, tables)

    def test_privileged_functions_fix_search_path_and_revoke_browser_access(self) -> None:
        functions = re.findall(
            r"create or replace function public\.([a-z_]+)\((.*?)\n\$\$;",
            self.schema,
            re.S,
        )
        privileged = {
            name: body
            for name, body in functions
            if "security definer" in body
        }

        self.assertTrue(privileged)
        for name, body in privileged.items():
            with self.subTest(function=name):
                self.assertIn("set search_path = ''", body)
                self.assertRegex(
                    self.schema,
                    rf"revoke all on function public\.{name}\([\s\S]+?\)\s+from public, anon, authenticated;",
                )

    def test_no_public_or_anonymous_table_policy_is_created(self) -> None:
        self.assertNotRegex(
            self.schema,
            r"create policy .*?\s+to\s+(?:public|anon)(?:\s|,)",
        )


if __name__ == "__main__":
    unittest.main()
