from __future__ import annotations

import json
import os
from ipaddress import ip_address
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sph.security import is_bearer_secret, normalize_https_origin, supabase_headers


class HttpTransport(Protocol):
    def __call__(
        self,
        method: str,
        path: str,
        payload: object | None = None,
    ) -> object: ...


class PushSender(Protocol):
    def __call__(self, subscription: dict[str, object], payload: str) -> None: ...


class PushSubscriptionError(ValueError):
    pass


@dataclass(frozen=True)
class PushDeliveryConfig:
    enabled: bool
    supabase_url: str
    service_role_key: str
    vapid_private_key: str
    vapid_subject: str
    cron_secret: str

    @classmethod
    def from_environment(cls) -> "PushDeliveryConfig":
        return cls(
            enabled=os.getenv("PUSH_DELIVERY_READY", "").strip().lower() in {"1", "true", "yes"},
            supabase_url=normalize_https_origin(os.getenv("SUPABASE_URL", "")),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
            vapid_private_key=os.getenv("VAPID_PRIVATE_KEY", "").strip(),
            vapid_subject=os.getenv("VAPID_SUBJECT", "").strip(),
            cron_secret=os.getenv("PUSH_CRON_SECRET", "").strip(),
        )

    def validate(self) -> None:
        if not self.enabled:
            raise RuntimeError("A entrega push ainda não está ativa.")
        missing = [
            name
            for name, value in {
                "SUPABASE_URL": normalize_https_origin(self.supabase_url),
                "SUPABASE_SERVICE_ROLE_KEY": self.service_role_key,
                "VAPID_PRIVATE_KEY": self.vapid_private_key,
                "VAPID_SUBJECT": self.vapid_subject,
                "PUSH_CRON_SECRET": self.cron_secret,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Configuração push incompleta: {', '.join(missing)}")


def is_authorized(authorization: str | None, expected_secret: str) -> bool:
    return is_bearer_secret(authorization, expected_secret)


def _local_due(preference: dict[str, object], now_utc: datetime) -> tuple[bool, str]:
    timezone_name = str(preference.get("timezone") or "Atlantic/Cape_Verde")
    try:
        local_now = now_utc.astimezone(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        return False, ""

    local_time = str(preference.get("local_time") or "07:00")
    expected = local_time[:5]
    local_day = local_now.date().isoformat()
    return (
        local_now.strftime("%H:%M") == expected
        and str(preference.get("last_sent_on") or "") != local_day,
        local_day,
    )


def _clean_push_key(value: object, minimum: int, maximum: int) -> str:
    cleaned = value.strip() if isinstance(value, str) else ""
    if not minimum <= len(cleaned) <= maximum:
        raise PushSubscriptionError("Chave push inválida")
    if any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-=" for character in cleaned):
        raise PushSubscriptionError("Chave push inválida")
    if "=" in cleaned.rstrip("=") or len(cleaned) - len(cleaned.rstrip("=")) > 2:
        raise PushSubscriptionError("Chave push inválida")
    return cleaned


def _subscription_payload(row: dict[str, object]) -> dict[str, object]:
    endpoint = row.get("endpoint")
    if not isinstance(endpoint, str) or not endpoint.strip() or len(endpoint.strip()) > 2048:
        raise PushSubscriptionError("Endpoint push inválido")
    try:
        parsed = urlsplit(endpoint.strip())
        _ = parsed.port
    except ValueError as exc:
        raise PushSubscriptionError("Endpoint push inválido") from exc
    hostname = (parsed.hostname or "").lower()
    private_hostname = (
        hostname == "localhost"
        or hostname.endswith((".localhost", ".local", ".internal"))
    )
    try:
        private_address = ip_address(hostname).is_private or ip_address(hostname).is_loopback
    except ValueError:
        private_address = False
    if (
        parsed.scheme.lower() != "https"
        or not hostname
        or parsed.username
        or parsed.password
        or private_hostname
        or private_address
    ):
        raise PushSubscriptionError("Endpoint push inválido")
    return {
        "endpoint": endpoint.strip(),
        "keys": {
            "p256dh": _clean_push_key(row.get("p256dh"), 16, 512),
            "auth": _clean_push_key(row.get("auth_secret"), 8, 256),
        },
    }


def _delivery_rpc(
    request: HttpTransport,
    action: str,
    user_id: str,
    local_day: str,
    timestamp: datetime,
) -> bool:
    time_parameter = {
        "claim": "p_claimed_at",
        "complete": "p_completed_at",
        "release": "p_released_at",
    }[action]
    result = request(
        "POST",
        f"/rest/v1/rpc/{action}_push_delivery",
        {
            "p_user_id": user_id,
            "p_local_day": local_day,
            time_parameter: timestamp.isoformat(),
        },
    )
    return result is True


def deliver_due_notifications(
    config: PushDeliveryConfig,
    *,
    now_utc: datetime | None = None,
    transport: HttpTransport | None = None,
    send_push: PushSender | None = None,
) -> dict[str, int]:
    config.validate()
    current_time = now_utc or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    request = transport or SupabaseRestTransport(config)
    sender = send_push or WebPushSender(config)
    stats = {"due": 0, "sent": 0, "expired": 0, "failed": 0}

    preferences = request(
        "GET",
        "/rest/v1/notification_preferences"
        "?select=user_id,local_time,timezone,last_sent_on&enabled=eq.true",
    )
    if not isinstance(preferences, list):
        raise RuntimeError("Resposta inválida ao carregar preferências push")

    message = json.dumps(
        {
            "title": "Só Por Hoje",
            "body": "A meditação de hoje está pronta. Um dia de cada vez.",
            "url": "/#meditacao",
        },
        ensure_ascii=False,
    )

    for preference in preferences:
        if not isinstance(preference, dict):
            continue
        due, local_day = _local_due(preference, current_time)
        if not due:
            continue
        raw_user_id = str(preference.get("user_id") or "")
        if not raw_user_id or not _delivery_rpc(request, "claim", raw_user_id, local_day, current_time):
            continue
        stats["due"] += 1
        user_id = quote(raw_user_id, safe="")
        subscriptions = request(
            "GET",
            "/rest/v1/push_subscriptions"
            f"?select=id,endpoint,p256dh,auth_secret&user_id=eq.{user_id}&active=eq.true",
        )
        if not isinstance(subscriptions, list):
            stats["failed"] += 1
            _delivery_rpc(request, "release", raw_user_id, local_day, current_time)
            continue
        sent_for_user = False
        transient_failure = False
        for subscription in subscriptions:
            if not isinstance(subscription, dict):
                continue
            try:
                sender(_subscription_payload(subscription), message)
                stats["sent"] += 1
                sent_for_user = True
            except Exception as exc:  # The push library exposes status through response.status_code.
                malformed = isinstance(exc, PushSubscriptionError)
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if malformed or status_code in {404, 410}:
                    subscription_id = quote(str(subscription.get("id") or ""), safe="")
                    if subscription_id:
                        request(
                            "PATCH",
                            f"/rest/v1/push_subscriptions?id=eq.{subscription_id}",
                            {"active": False, "updated_at": current_time.isoformat()},
                        )
                    stats["expired"] += 1
                else:
                    stats["failed"] += 1
                    transient_failure = True

        if sent_for_user:
            _delivery_rpc(request, "complete", raw_user_id, local_day, current_time)
        elif transient_failure:
            _delivery_rpc(request, "release", raw_user_id, local_day, current_time)
        else:
            request(
                "PATCH",
                f"/rest/v1/notification_preferences?user_id=eq.{user_id}",
                {
                    "enabled": False,
                    "delivery_claimed_on": None,
                    "delivery_claimed_at": None,
                    "updated_at": current_time.isoformat(),
                },
            )

    return stats


class SupabaseRestTransport:
    def __init__(self, config: PushDeliveryConfig) -> None:
        self.config = config

    def __call__(self, method: str, path: str, payload: object | None = None) -> object:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.config.supabase_url}{path}",
            data=body,
            method=method,
            headers={
                **supabase_headers(self.config.service_role_key),
                "Prefer": "return=minimal" if method == "PATCH" else "",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
        except HTTPError as exc:
            raise RuntimeError(f"Supabase respondeu com HTTP {exc.code}") from exc
        return json.loads(raw) if raw else None


class WebPushSender:
    def __init__(self, config: PushDeliveryConfig) -> None:
        self.config = config

    def __call__(self, subscription: dict[str, object], payload: str) -> None:
        from pywebpush import webpush

        webpush(
            subscription_info=subscription,
            data=payload,
            vapid_private_key=self.config.vapid_private_key,
            vapid_claims={"sub": self.config.vapid_subject},
        )
