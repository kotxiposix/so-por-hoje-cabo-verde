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

    payload: dict[str, object] = {
        "features": {
            "account": account_enabled,
            "community": False,
            "push": False,
        }
    }
    if account_enabled:
        payload["supabase"] = {
            "url": supabase_url,
            "publishableKey": publishable_key,
        }
    return payload
