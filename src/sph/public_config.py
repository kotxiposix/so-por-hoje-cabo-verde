from __future__ import annotations

import os
from collections.abc import Mapping


def public_runtime_config(environment: Mapping[str, str] | None = None) -> dict[str, object]:
    env = environment or os.environ
    supabase_url = env.get("SUPABASE_URL", "").strip().rstrip("/")
    publishable_key = (
        env.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or env.get("SUPABASE_ANON_KEY", "").strip()
    )
    account_enabled = bool(supabase_url and publishable_key)
    vapid_public_key = env.get("VAPID_PUBLIC_KEY", "").strip()
    delivery_ready = env.get("PUSH_DELIVERY_READY", "").strip().lower() in {"1", "true", "yes"}
    push_enabled = bool(account_enabled and vapid_public_key and delivery_ready)
    ai_ready = env.get("AI_DELIVERY_READY", "").strip().lower() in {"1", "true", "yes"}
    ai_enabled = bool(
        account_enabled
        and ai_ready
        and env.get("OPENAI_API_KEY", "").strip()
        and env.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )

    payload: dict[str, object] = {
        "features": {
            "account": account_enabled,
            "community": False,
            "push": push_enabled,
            "ai": ai_enabled,
        }
    }
    if account_enabled:
        payload["supabase"] = {
            "url": supabase_url,
            "publishableKey": publishable_key,
        }
    if push_enabled:
        payload["push"] = {"vapidPublicKey": vapid_public_key}
    return payload
