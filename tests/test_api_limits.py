from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from pydantic import ValidationError

from sph.api import AiDailySupportPayload
from sph.send_log import JsonlSendLog, SendLogEntry
from sph.simple_server import (
    Handler,
    MAX_JSON_BODY_BYTES,
    NO_STORE,
    PUBLIC_DIR,
    REVALIDATE,
    SECURITY_HEADERS,
    RequestBodyTooLarge,
)


class ApiLimitTests(unittest.TestCase):
    def test_simple_server_rejects_excessive_json_body_before_reading(self) -> None:
        handler = Handler.__new__(Handler)
        handler.headers = {"Content-Length": str(MAX_JSON_BODY_BYTES + 1)}
        handler.rfile = io.BytesIO(b"{}")

        with self.assertRaises(RequestBodyTooLarge):
            handler.read_json_body()

        self.assertEqual(handler.rfile.tell(), 0)

    def test_simple_server_accepts_small_json_object(self) -> None:
        handler = Handler.__new__(Handler)
        body = b'{"user_state":"standard"}'
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile = io.BytesIO(body)

        self.assertEqual(handler.read_json_body(), {"user_state": "standard"})

    def test_simple_server_serves_only_files_inside_public_directory(self) -> None:
        handler = Handler.__new__(Handler)

        self.assertTrue(handler._is_public_file(PUBLIC_DIR / "index.html"))
        self.assertFalse(handler._is_public_file(PUBLIC_DIR.parent / "README.md"))

    def test_simple_server_json_responses_are_private_and_protected(self) -> None:
        handler = Handler.__new__(Handler)
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = io.BytesIO()

        handler.respond({"status": "ok"})

        handler.send_header.assert_any_call("Cache-Control", NO_STORE)
        for key, value in SECURITY_HEADERS.items():
            handler.send_header.assert_any_call(key, value)
        handler.send_header.assert_any_call("Content-Type", "application/json; charset=utf-8")

    def test_simple_server_static_cache_policy_matches_sensitive_routes(self) -> None:
        self.assertEqual(Handler.static_cache_control("/sw.js"), REVALIDATE)
        self.assertEqual(Handler.static_cache_control("/admin"), NO_STORE)
        self.assertEqual(Handler.static_cache_control("/admin/admin.js"), NO_STORE)
        self.assertEqual(Handler.static_cache_control("/assets/app.js"), REVALIDATE)

    def test_simple_server_adds_utf8_to_textual_content_types(self) -> None:
        self.assertEqual(
            Handler.content_type(Path("app.js"), "text/javascript"),
            "text/javascript; charset=utf-8",
        )
        self.assertEqual(Handler.content_type(Path("hero.jpg"), "image/jpeg"), "image/jpeg")

    def test_simple_server_security_headers_match_vercel(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "vercel.json").read_text(encoding="utf-8"))
        rules = {
            rule["source"]: {item["key"]: item["value"] for item in rule["headers"]}
            for rule in config["headers"]
        }
        vercel_security = rules["/(.*)"].copy()
        vercel_security.pop("Strict-Transport-Security")

        self.assertEqual(SECURITY_HEADERS, vercel_security)

    def test_ai_payload_rejects_negative_or_excessive_progress(self) -> None:
        with self.assertRaises(ValidationError):
            AiDailySupportPayload(clean_days=-1)
        with self.assertRaises(ValidationError):
            AiDailySupportPayload(reading_streak=3_661)

    def test_ai_payload_rejects_unexpected_daily_fields(self) -> None:
        with self.assertRaises(ValidationError):
            AiDailySupportPayload(
                daily={
                    "date": "2026-01-01",
                    "weekday": "Quinta-feira",
                    "month_day": "01-01",
                    "title": "Título",
                    "body": "Corpo",
                    "reflection": "Reflexão",
                    "source": "campo não aceite",
                }
            )

    def test_send_log_limit_returns_latest_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = JsonlSendLog(Path(directory) / "send.jsonl")
            for day in range(1, 4):
                log.append(
                    SendLogEntry(
                        send_date=f"2026-01-0{day}",
                        month_day=f"01-0{day}",
                        channel="console",
                        destination_id=None,
                        status="sent",
                        message_hash=str(day),
                        error_message=None,
                        sent_at=f"2026-01-0{day}T08:00:00-01:00",
                    )
                )

            self.assertEqual(
                [entry.send_date for entry in log.list(limit=2)],
                ["2026-01-02", "2026-01-03"],
            )


if __name__ == "__main__":
    unittest.main()
