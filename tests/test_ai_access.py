from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from sph.ai_access import AiRuntimeConfig, SupabaseAiUsage


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class AiAccessTests(unittest.TestCase):
    def test_runtime_requires_explicit_flag_and_all_private_values(self) -> None:
        base = {
            "SUPABASE_URL": "https://project.supabase.co/",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "OPENAI_API_KEY": "openai-secret",
        }
        with patch.dict(os.environ, base, clear=True):
            self.assertFalse(AiRuntimeConfig.from_environment().ready)

        with patch.dict(os.environ, {**base, "AI_DELIVERY_READY": "true"}, clear=True):
            config = AiRuntimeConfig.from_environment()

        self.assertTrue(config.ready)
        self.assertEqual(config.supabase_url, "https://project.supabase.co")

    def test_daily_limit_is_bounded_and_invalid_values_use_default(self) -> None:
        with patch.dict(os.environ, {"AI_DAILY_LIMIT": "100"}, clear=True):
            self.assertEqual(AiRuntimeConfig.from_environment().daily_limit, 20)
        with patch.dict(os.environ, {"AI_DAILY_LIMIT": "invalid"}, clear=True):
            self.assertEqual(AiRuntimeConfig.from_environment().daily_limit, 3)

    def test_claim_uses_service_role_and_configured_limit(self) -> None:
        config = AiRuntimeConfig(
            enabled=True,
            supabase_url="https://project.supabase.co",
            service_role_key="service-role",
            openai_api_key="openai-secret",
            daily_limit=4,
        )

        with patch("sph.ai_access.urlopen", return_value=FakeResponse(True)) as urlopen_mock:
            claimed = SupabaseAiUsage(config).claim("user-123")

        self.assertTrue(claimed)
        request = urlopen_mock.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://project.supabase.co/rest/v1/rpc/claim_ai_daily_request",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer service-role")
        self.assertEqual(
            json.loads(request.data),
            {"p_user_id": "user-123", "p_limit": 4},
        )


if __name__ == "__main__":
    unittest.main()
