from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


class AccountAuthenticationError(RuntimeError):
    pass


class AccountServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class AccountDeletionConfig:
    supabase_url: str
    service_role_key: str

    @classmethod
    def from_environment(cls) -> "AccountDeletionConfig":
        return cls(
            supabase_url=os.getenv("SUPABASE_URL", "").strip().rstrip("/"),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        )

    def validate(self) -> None:
        if not self.supabase_url or not self.service_role_key:
            raise AccountServiceError("A eliminação de conta ainda não está configurada.")


def bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise AccountAuthenticationError("Sessão em falta.")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token:
        raise AccountAuthenticationError("Sessão inválida.")
    return token


class SupabaseAccountDeletion:
    def __init__(self, config: AccountDeletionConfig) -> None:
        config.validate()
        self.config = config

    def delete_for_access_token(self, access_token: str) -> str:
        user = self._request(
            "GET",
            "/auth/v1/user",
            authorization=access_token,
            authentication_request=True,
        )
        user_id = user.get("id") if isinstance(user, dict) else None
        if not isinstance(user_id, str) or not user_id:
            raise AccountAuthenticationError("A sessão não identifica uma conta válida.")
        self._request(
            "DELETE",
            f"/auth/v1/admin/users/{quote(user_id, safe='')}",
            authorization=self.config.service_role_key,
        )
        return user_id

    def _request(
        self,
        method: str,
        path: str,
        *,
        authorization: str,
        authentication_request: bool = False,
    ) -> object:
        request = Request(
            f"{self.config.supabase_url}{path}",
            method=method,
            headers={
                "apikey": self.config.service_role_key,
                "Authorization": f"Bearer {authorization}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
        except HTTPError as exc:
            if authentication_request and exc.code in {401, 403}:
                raise AccountAuthenticationError("A sessão expirou ou deixou de ser válida.") from exc
            raise AccountServiceError(f"Supabase respondeu com HTTP {exc.code}") from exc
        return json.loads(raw) if raw else {}
