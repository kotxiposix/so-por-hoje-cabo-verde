from __future__ import annotations

import json
import unittest

from scripts.check_supabase_schema import EXPECTED_OBJECTS, probe_supabase_schema


class FakeResponse:
    def __init__(self, document: dict[str, object]) -> None:
        self.payload = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class SupabaseSchemaCheckTests(unittest.TestCase):
    def test_missing_configuration_does_not_call_network(self) -> None:
        def fail_if_called(*args: object, **kwargs: object) -> None:
            raise AssertionError("network should not be called")

        report = probe_supabase_schema({}, opener=fail_if_called)

        self.assertFalse(report.configured)
        self.assertFalse(report.reachable)
        self.assertEqual(report.error, "missing_configuration")

    def test_complete_openapi_schema_marks_every_feature_complete(self) -> None:
        paths = {
            path: {"get": {}}
            for expected in EXPECTED_OBJECTS.values()
            for path in expected
        }

        def opener(request: object, timeout: int) -> FakeResponse:
            self.assertEqual(timeout, 15)
            return FakeResponse({"openapi": "3.0.0", "paths": paths})

        report = probe_supabase_schema(
            {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "private-service-key",
            },
            opener=opener,
        )

        self.assertTrue(report.configured)
        self.assertTrue(report.reachable)
        self.assertTrue(all(item["complete"] for item in report.features.values()))
        self.assertNotIn("private-service-key", repr(report))

    def test_missing_rpc_is_reported_only_for_affected_feature(self) -> None:
        paths = {
            path: {"get": {}}
            for expected in EXPECTED_OBJECTS.values()
            for path in expected
            if path != "/rpc/submit_anonymous_post"
        }

        report = probe_supabase_schema(
            {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "private-service-key",
            },
            opener=lambda *args, **kwargs: FakeResponse({"paths": paths}),
        )

        self.assertFalse(report.features["community"]["complete"])
        self.assertEqual(
            report.features["community"]["missing"],
            ["/rpc/submit_anonymous_post"],
        )
        self.assertTrue(report.features["account"]["complete"])

    def test_non_https_project_url_is_rejected(self) -> None:
        report = probe_supabase_schema(
            {
                "SUPABASE_URL": "http://project.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "private-service-key",
            }
        )

        self.assertFalse(report.reachable)
        self.assertEqual(report.error, "invalid_supabase_url")


if __name__ == "__main__":
    unittest.main()
