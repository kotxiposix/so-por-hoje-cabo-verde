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
    account_ready = env.get("ACCOUNT_READY", "").strip().lower() in {"1", "true", "yes"}
    account_enabled = bool(account_ready and supabase_url and publishable_key)
    staff_access_ready = env.get("STAFF_ACCESS_READY", "").strip().lower() in {"1", "true", "yes"}
    staff_admin_enabled = bool(
        staff_access_ready
        and supabase_url
        and publishable_key
        and env.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    vapid_public_key = env.get("VAPID_PUBLIC_KEY", "").strip()
    delivery_ready = env.get("PUSH_DELIVERY_READY", "").strip().lower() in {"1", "true", "yes"}
    push_enabled = bool(
        account_enabled
        and delivery_ready
        and vapid_public_key
        and env.get("VAPID_PRIVATE_KEY", "").strip()
        and env.get("VAPID_SUBJECT", "").strip()
        and env.get("PUSH_CRON_SECRET", "").strip()
        and env.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    ai_ready = env.get("AI_DELIVERY_READY", "").strip().lower() in {"1", "true", "yes"}
    ai_enabled = bool(
        account_enabled
        and ai_ready
        and env.get("OPENAI_API_KEY", "").strip()
        and env.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    community_ready = env.get("COMMUNITY_READY", "").strip().lower() in {"1", "true", "yes"}
    community_enabled = bool(
        account_enabled
        and community_ready
        and staff_access_ready
        and env.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    help_directory_ready = env.get("HELP_DIRECTORY_READY", "").strip().lower() in {"1", "true", "yes"}
    help_directory_enabled = bool(
        help_directory_ready
        and staff_access_ready
        and supabase_url
        and env.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )

    payload: dict[str, object] = {
        "features": {
            "account": account_enabled,
            "staffAdmin": staff_admin_enabled,
            "community": community_enabled,
            "helpDirectory": help_directory_enabled,
            "push": push_enabled,
            "ai": ai_enabled,
        }
    }
    if account_enabled or staff_admin_enabled:
        payload["supabase"] = {
            "url": supabase_url,
            "publishableKey": publishable_key,
        }
    if push_enabled:
        payload["push"] = {"vapidPublicKey": vapid_public_key}
    return payload
