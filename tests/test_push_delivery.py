from __future__ import annotations

import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from sph.push_delivery import PushDeliveryConfig, deliver_due_notifications, is_authorized


class ExpiredPushError(Exception):
    def __init__(self) -> None:
        self.response = type("Response", (), {"status_code": 410})()


class PushDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PushDeliveryConfig(
            enabled=True,
            supabase_url="https://project.supabase.co",
            service_role_key="service-secret",
            vapid_private_key="private-vapid",
            vapid_subject="mailto:team@example.com",
            cron_secret="cron-secret",
        )

    def test_delivery_flag_blocks_transport_even_when_secrets_exist(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-secret",
            "VAPID_PRIVATE_KEY": "private-vapid",
            "VAPID_SUBJECT": "mailto:team@example.com",
            "PUSH_CRON_SECRET": "cron-secret",
        }
        with patch.dict(os.environ, environment, clear=True):
            config = PushDeliveryConfig.from_environment()

        self.assertFalse(config.enabled)
        with self.assertRaisesRegex(RuntimeError, "ainda não está ativa"):
            deliver_due_notifications(
                config,
                transport=lambda *_args, **_kwargs: self.fail("Supabase não deve ser consultado"),
                send_push=lambda *_args, **_kwargs: self.fail("Push não deve ser enviado"),
            )

    def test_authorization_requires_exact_bearer_secret(self) -> None:
        self.assertTrue(is_authorized("Bearer cron-secret", "cron-secret"))
        self.assertFalse(is_authorized("Bearer wrong", "cron-secret"))
        self.assertFalse(is_authorized(None, "cron-secret"))
        self.assertFalse(is_authorized("cron-secret", "cron-secret"))

    def test_due_notification_is_sent_once_and_marked(self) -> None:
        calls: list[tuple[str, str, object | None]] = []
        sent: list[tuple[dict[str, object], dict[str, str]]] = []

        def transport(method: str, path: str, payload: object | None = None) -> object:
            calls.append((method, path, payload))
            if "rpc/claim_push_delivery" in path:
                return True
            if "rpc/complete_push_delivery" in path:
                return True
            if "notification_preferences?select" in path:
                return [{
                    "user_id": "user-one",
                    "local_time": "07:00:00",
                    "timezone": "Atlantic/Cape_Verde",
                    "last_sent_on": None,
                }]
            if "push_subscriptions?select" in path:
                return [{
                    "id": "subscription-one",
                    "endpoint": "https://push.example/one",
                    "p256dh": "client-key",
                    "auth_secret": "auth-secret",
                }]
            return None

        def send_push(subscription: dict[str, object], payload: str) -> None:
            sent.append((subscription, json.loads(payload)))

        result = deliver_due_notifications(
            self.config,
            now_utc=datetime(2026, 9, 26, 8, 0, tzinfo=timezone.utc),
            transport=transport,
            send_push=send_push,
        )

        self.assertEqual(result, {"due": 1, "sent": 1, "expired": 0, "failed": 0})
        self.assertEqual(sent[0][1], {
            "title": "Só Por Hoje",
            "body": "A meditação de hoje está pronta. Um dia de cada vez.",
            "url": "/#meditacao",
        })
        self.assertNotIn("user-one", sent[0][1].values())
        self.assertIn((
            "POST",
            "/rest/v1/rpc/complete_push_delivery",
            {
                "p_user_id": "user-one",
                "p_local_day": "2026-09-26",
                "p_completed_at": "2026-09-26T08:00:00+00:00",
            },
        ), calls)

    def test_already_sent_preference_is_skipped(self) -> None:
        def transport(method: str, path: str, payload: object | None = None) -> object:
            return [{
                "user_id": "user-one",
                "local_time": "07:00:00",
                "timezone": "Atlantic/Cape_Verde",
                "last_sent_on": "2026-09-26",
            }]

        result = deliver_due_notifications(
            self.config,
            now_utc=datetime(2026, 9, 26, 8, 0, tzinfo=timezone.utc),
            transport=transport,
            send_push=lambda *_: self.fail("A notification should not be sent twice"),
        )

        self.assertEqual(result["due"], 0)

    def test_expired_subscription_is_deactivated_without_marking_day(self) -> None:
        calls: list[tuple[str, str, object | None]] = []

        def transport(method: str, path: str, payload: object | None = None) -> object:
            calls.append((method, path, payload))
            if "rpc/claim_push_delivery" in path:
                return True
            if "notification_preferences?select" in path:
                return [{
                    "user_id": "user-one",
                    "local_time": "07:00:00",
                    "timezone": "Atlantic/Cape_Verde",
                    "last_sent_on": None,
                }]
            if "push_subscriptions?select" in path:
                return [{
                    "id": "subscription-one",
                    "endpoint": "https://push.example/expired",
                    "p256dh": "client-key",
                    "auth_secret": "auth-secret",
                }]
            return None

        result = deliver_due_notifications(
            self.config,
            now_utc=datetime(2026, 9, 26, 8, 0, tzinfo=timezone.utc),
            transport=transport,
            send_push=lambda *_: (_ for _ in ()).throw(ExpiredPushError()),
        )

        self.assertEqual(result["expired"], 1)
        self.assertIn(
            (
                "PATCH",
                "/rest/v1/push_subscriptions?id=eq.subscription-one",
                {"active": False, "updated_at": "2026-09-26T08:00:00+00:00"},
            ),
            calls,
        )
        self.assertIn(
            (
                "PATCH",
                "/rest/v1/notification_preferences?user_id=eq.user-one",
                {
                    "enabled": False,
                    "delivery_claimed_on": None,
                    "delivery_claimed_at": None,
                    "updated_at": "2026-09-26T08:00:00+00:00",
                },
            ),
            calls,
        )

    def test_overlapping_delivery_cannot_claim_the_same_user_twice(self) -> None:
        calls: list[tuple[str, str, object | None]] = []

        def transport(method: str, path: str, payload: object | None = None) -> object:
            calls.append((method, path, payload))
            if "notification_preferences?select" in path:
                return [{
                    "user_id": "user-one",
                    "local_time": "07:00:00",
                    "timezone": "Atlantic/Cape_Verde",
                    "last_sent_on": None,
                }]
            if "rpc/claim_push_delivery" in path:
                return False
            self.fail(f"Unexpected request after rejected claim: {method} {path}")

        result = deliver_due_notifications(
            self.config,
            now_utc=datetime(2026, 9, 26, 8, 0, tzinfo=timezone.utc),
            transport=transport,
            send_push=lambda *_: self.fail("Push must not be sent without the atomic claim"),
        )

        self.assertEqual(result, {"due": 0, "sent": 0, "expired": 0, "failed": 0})
        self.assertTrue(any("rpc/claim_push_delivery" in path for _, path, _ in calls))

    def test_transient_failure_releases_claim_for_a_later_retry(self) -> None:
        calls: list[tuple[str, str, object | None]] = []

        def transport(method: str, path: str, payload: object | None = None) -> object:
            calls.append((method, path, payload))
            if "notification_preferences?select" in path:
                return [{
                    "user_id": "user-one",
                    "local_time": "07:00:00",
                    "timezone": "Atlantic/Cape_Verde",
                    "last_sent_on": None,
                }]
            if "rpc/claim_push_delivery" in path or "rpc/release_push_delivery" in path:
                return True
            if "push_subscriptions?select" in path:
                return [{
                    "id": "subscription-one",
                    "endpoint": "https://push.example/temporary-failure",
                    "p256dh": "client-key",
                    "auth_secret": "auth-secret",
                }]
            return None

        result = deliver_due_notifications(
            self.config,
            now_utc=datetime(2026, 9, 26, 8, 0, tzinfo=timezone.utc),
            transport=transport,
            send_push=lambda *_: (_ for _ in ()).throw(RuntimeError("temporary")),
        )

        self.assertEqual(result["failed"], 1)
        self.assertIn((
            "POST",
            "/rest/v1/rpc/release_push_delivery",
            {
                "p_user_id": "user-one",
                "p_local_day": "2026-09-26",
                "p_released_at": "2026-09-26T08:00:00+00:00",
            },
        ), calls)


if __name__ == "__main__":
    unittest.main()
