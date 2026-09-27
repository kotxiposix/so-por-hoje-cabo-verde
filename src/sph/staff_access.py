from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID

from sph.account_deletion import AccountAuthenticationError, bearer_token


class StaffAuthenticationError(RuntimeError):
    pass


class StaffForbiddenError(RuntimeError):
    pass


class StaffAccessServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class StaffAccessConfig:
    enabled: bool
    supabase_url: str
    service_role_key: str

    @classmethod
    def from_environment(cls) -> "StaffAccessConfig":
        return cls(
            enabled=os.getenv("STAFF_ACCESS_READY", "").strip().lower() in {"1", "true", "yes"},
            supabase_url=os.getenv("SUPABASE_URL", "").strip().rstrip("/"),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        )

    @property
    def ready(self) -> bool:
        return bool(self.enabled and self.supabase_url and self.service_role_key)

    def validate(self) -> None:
        if not self.ready:
            raise StaffAccessServiceError("O acesso individual da equipa ainda não está ativo.")


@dataclass(frozen=True)
class StaffIdentity:
    user_id: str
    roles: tuple[str, ...]


class SupabaseStaffAccess:
    VALID_ROLES = {"admin", "moderator", "help_editor"}

    def __init__(self, config: StaffAccessConfig) -> None:
        config.validate()
        self.config = config

    def authorize(
        self,
        authorization: str | None,
        allowed_roles: set[str],
    ) -> StaffIdentity:
        invalid_roles = allowed_roles.difference(self.VALID_ROLES)
        if not allowed_roles or invalid_roles:
            raise ValueError("Papéis de equipa inválidos.")
        try:
            access_token = bearer_token(authorization)
        except AccountAuthenticationError as exc:
            raise StaffAuthenticationError(str(exc)) from exc
        user = self._request(
            "GET",
            "/auth/v1/user",
            authorization=access_token,
        )
        user_id = user.get("id") if isinstance(user, dict) else None
        try:
            normalized_user_id = str(UUID(user_id))
        except (AttributeError, TypeError, ValueError) as exc:
            raise StaffAuthenticationError("A sessão não identifica uma conta válida.") from exc
        records = self._request(
            "GET",
            "/rest/v1/staff_roles"
            f"?select=role&user_id=eq.{quote(normalized_user_id, safe='')}"
            "&status=eq.active",
            authorization=self.config.service_role_key,
        )
        if not isinstance(records, list):
            raise StaffAccessServiceError("A autorização da equipa devolveu uma resposta inválida.")
        roles = tuple(sorted({
            record.get("role")
            for record in records
            if isinstance(record, dict) and record.get("role") in self.VALID_ROLES
        }))
        if "admin" not in roles and not allowed_roles.intersection(roles):
            raise StaffForbiddenError("Esta conta não tem permissão para esta área.")
        return StaffIdentity(user_id=normalized_user_id, roles=roles)

    def _request(self, method: str, path: str, *, authorization: str) -> object:
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
            if path == "/auth/v1/user" and exc.code in {401, 403}:
                raise StaffAuthenticationError("A sessão expirou ou deixou de ser válida.") from exc
            raise StaffAccessServiceError(f"Supabase respondeu com HTTP {exc.code}") from exc
        except OSError as exc:
            raise StaffAccessServiceError("Não foi possível validar o acesso da equipa.") from exc
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise StaffAccessServiceError("A autorização da equipa devolveu uma resposta inválida.") from exc
