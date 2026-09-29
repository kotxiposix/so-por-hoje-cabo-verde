from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sph.security import is_safe_https_origin, normalize_https_origin, supabase_headers


class AiUsageError(RuntimeError):
    pass


@dataclass(frozen=True)
class AiRuntimeConfig:
    enabled: bool
    supabase_url: str
    service_role_key: str
    openai_api_key: str
    daily_limit: int

    @classmethod
    def from_environment(cls) -> "AiRuntimeConfig":
        enabled = os.getenv("AI_DELIVERY_READY", "").strip().lower() in {"1", "true", "yes"}
        try:
            daily_limit = max(1, min(int(os.getenv("AI_DAILY_LIMIT", "3")), 20))
        except ValueError:
            daily_limit = 3
        return cls(
            enabled=enabled,
            supabase_url=normalize_https_origin(os.getenv("SUPABASE_URL", "")),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            daily_limit=daily_limit,
        )

    @property
    def ready(self) -> bool:
        return bool(
            self.enabled
            and is_safe_https_origin(self.supabase_url)
            and self.service_role_key
            and self.openai_api_key
        )


class SupabaseAiUsage:
    def __init__(self, config: AiRuntimeConfig) -> None:
        self.config = config

    def claim(self, user_id: str) -> bool:
        if not self.config.ready:
            return False
        body = json.dumps({
            "p_user_id": user_id,
            "p_limit": self.config.daily_limit,
        }).encode("utf-8")
        request = Request(
            f"{self.config.supabase_url}/rest/v1/rpc/claim_ai_daily_request",
            data=body,
            method="POST",
            headers=supabase_headers(self.config.service_role_key),
        )
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read() or b"false")
        except (HTTPError, OSError, json.JSONDecodeError) as exc:
            raise AiUsageError("Não foi possível reservar a utilização de AI.") from exc
        return payload is True
