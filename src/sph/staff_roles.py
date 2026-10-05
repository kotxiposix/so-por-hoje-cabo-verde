from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID

from sph.security import supabase_headers
from sph.staff_access import StaffAccessConfig


class StaffRoleInputError(ValueError):
    pass


class StaffRoleConflictError(RuntimeError):
    pass


class StaffRoleServiceError(RuntimeError):
    pass


VALID_ROLES = {"admin", "moderator", "help_editor", "content_editor"}
VALID_STATUSES = {"active", "suspended"}


def normalize_email(value: object) -> str:
    email = str(value or "").strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise StaffRoleInputError("Email inválido.")
    return email


def normalize_role(value: object) -> str:
    role = str(value or "").strip()
    if role not in VALID_ROLES:
        raise StaffRoleInputError("Papel de equipa inválido.")
    return role


def normalize_status(value: object) -> str:
    status = str(value or "").strip()
    if status not in VALID_STATUSES:
        raise StaffRoleInputError("Estado do papel inválido.")
    return status


def public_staff_role(record: object) -> dict[str, str]:
    if not isinstance(record, dict):
        raise StaffRoleServiceError("A gestão da equipa devolveu uma resposta inválida.")
    try:
        user_id = str(UUID(str(record.get("user_id") or "")))
    except (TypeError, ValueError) as exc:
        raise StaffRoleServiceError("A gestão da equipa devolveu uma conta inválida.") from exc
    updated_at = str(record.get("updated_at") or "")
    try:
        parsed_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StaffRoleServiceError("A gestão da equipa devolveu uma data inválida.") from exc
    if parsed_at.tzinfo is None:
        raise StaffRoleServiceError("A gestão da equipa devolveu uma data inválida.")
    try:
        email = normalize_email(record.get("email"))
        role = normalize_role(record.get("role"))
        status = normalize_status(record.get("status"))
    except StaffRoleInputError as exc:
        raise StaffRoleServiceError("A gestão da equipa devolveu dados inválidos.") from exc
    return {
        "user_ref": f"Conta …{user_id[-6:]}",
        "email": email,
        "role": role,
        "status": status,
        "updated_at": updated_at,
    }


class SupabaseStaffRoles:
    def __init__(self, config: StaffAccessConfig) -> None:
        config.validate()
        self.config = config

    def list_roles(self, actor_id: str) -> list[dict[str, str]]:
        records = self._rpc("list_staff_roles", {"p_actor_id": self._uuid(actor_id)})
        if not isinstance(records, list):
            raise StaffRoleServiceError("A gestão da equipa devolveu uma resposta inválida.")
        visible: list[dict[str, str]] = []
        for record in records:
            visible.append(public_staff_role(record))
        return visible

    def set_role(
        self,
        actor_id: str,
        email: object,
        role: object,
        status: object,
    ) -> dict[str, str]:
        records = self._rpc(
            "manage_staff_role",
            {
                "p_actor_id": self._uuid(actor_id),
                "p_email": normalize_email(email),
                "p_role": normalize_role(role),
                "p_status": normalize_status(status),
            },
        )
        if not isinstance(records, list) or len(records) != 1:
            raise StaffRoleServiceError("A gestão da equipa devolveu uma resposta inválida.")
        return public_staff_role(records[0])

    @staticmethod
    def _uuid(value: str) -> str:
        try:
            return str(UUID(value))
        except (TypeError, ValueError) as exc:
            raise StaffRoleInputError("Conta administrativa inválida.") from exc

    def _rpc(self, name: str, payload: dict[str, object]) -> object:
        request = Request(
            f"{self.config.supabase_url}/rest/v1/rpc/{name}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=supabase_headers(self.config.service_role_key),
        )
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = self._error_detail(exc)
            if "Target account not found" in detail:
                raise StaffRoleInputError(
                    "A conta ainda não existe. A pessoa deve entrar primeiro na plataforma com este email."
                ) from exc
            if "Cannot suspend the last active administrator" in detail:
                raise StaffRoleConflictError(
                    "Não é possível suspender o último administrador ativo."
                ) from exc
            if "Actor is not an active administrator" in detail:
                raise StaffRoleConflictError("Esta conta deixou de ter permissão administrativa.") from exc
            raise StaffRoleServiceError(f"Supabase respondeu com HTTP {exc.code}") from exc
        except OSError as exc:
            raise StaffRoleServiceError("Não foi possível gerir os papéis da equipa.") from exc
        try:
            return json.loads(raw) if raw else []
        except json.JSONDecodeError as exc:
            raise StaffRoleServiceError("A gestão da equipa devolveu uma resposta inválida.") from exc

    @staticmethod
    def _error_detail(error: HTTPError) -> str:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return ""
        return str(payload.get("message") or payload.get("details") or "")
