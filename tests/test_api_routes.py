from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest.mock import patch

from sph.api import app


async def asgi_request(path: str, method: str = "GET") -> tuple[int, dict[str, str], object]:
    messages: list[dict[str, object]] = []
    request_sent = False

    async def receive() -> dict[str, object]:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "root_path": "",
    }
    await app(scope, receive, send)

    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    headers = {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in start.get("headers", [])
    }
    payload = json.loads(body.decode("utf-8")) if body else None
    return int(start["status"]), headers, payload


def request(path: str, method: str = "GET") -> tuple[int, dict[str, str], object]:
    return asyncio.run(asgi_request(path, method))


class ApiRouteContractTests(unittest.TestCase):
    def test_public_config_exposes_every_feature_as_closed_without_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            status, headers, payload = request("/api/v1/config")

        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "application/json")
        self.assertEqual(headers["cache-control"], "private, no-store")
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        self.assertEqual(headers["x-frame-options"], "DENY")
        self.assertIn("frame-ancestors 'none'", headers["content-security-policy"])
        self.assertEqual(
            payload,
            {
                "features": {
                    "account": False,
                    "staffAdmin": False,
                    "community": False,
                    "helpDirectory": False,
                    "editorialContent": False,
                    "push": False,
                    "ai": False,
                }
            },
        )

    def test_sensitive_public_catalogs_are_unavailable_while_flags_are_closed(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            results = {
                path: request(path)
                for path in (
                    "/api/v1/community/posts",
                    "/api/v1/help/resources",
                    "/api/v1/content",
                )
            }

        for path, (status, _headers, payload) in results.items():
            with self.subTest(path=path):
                self.assertEqual(status, 503)
                self.assertIn("ainda não", payload["detail"])

    def test_admin_and_internal_routes_reject_requests_without_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            staff_status, _headers, _payload = request("/api/v1/admin/me")
            technical_status, _headers, _payload = request("/api/v1/admin/send-logs")
            push_status, _headers, _payload = request(
                "/api/v1/internal/push/deliver",
                method="POST",
            )

        self.assertEqual(staff_status, 503)
        self.assertEqual(technical_status, 401)
        self.assertEqual(push_status, 401)

    def test_core_daily_routes_remain_available_without_integrations(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            health_status, _headers, health = request("/api/v1/health")
            today_status, _headers, today = request("/api/v1/today")

        self.assertEqual(health_status, 200)
        self.assertEqual(health["status"], "ok")
        self.assertEqual(today_status, 200)
        self.assertTrue(today["title"])
        self.assertRegex(today["month_day"], r"^\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
