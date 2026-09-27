from __future__ import annotations

import json
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID


class CommunityInputError(ValueError):
    pass


class CommunityConflictError(RuntimeError):
    pass


class CommunityLimitError(RuntimeError):
    pass


class CommunityServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommunityConfig:
    enabled: bool
    supabase_url: str
    service_role_key: str
    daily_post_limit: int = 3

    @classmethod
    def from_environment(cls) -> "CommunityConfig":
        try:
            daily_post_limit = max(
                1,
                min(int(os.getenv("COMMUNITY_DAILY_POST_LIMIT", "3")), 20),
            )
        except ValueError:
            daily_post_limit = 3
        return cls(
            enabled=os.getenv("COMMUNITY_READY", "").strip().lower() in {"1", "true", "yes"},
            supabase_url=os.getenv("SUPABASE_URL", "").strip().rstrip("/"),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
            daily_post_limit=daily_post_limit,
        )

    @property
    def ready(self) -> bool:
        return bool(self.enabled and self.supabase_url and self.service_role_key)

    def validate(self) -> None:
        if not self.ready:
            raise CommunityServiceError("A comunidade moderada ainda não está ativa.")


def normalize_post_body(value: str) -> str:
    body = " ".join(value.split())
    if not body:
        raise CommunityInputError("A partilha não pode ficar vazia.")
    if len(body) > 280:
        raise CommunityInputError("A partilha deve ter no máximo 280 caracteres.")
    return body


def normalize_details(value: str | None) -> str | None:
    if value is None:
        return None
    details = " ".join(value.split())
    if len(details) > 500:
        raise CommunityInputError("Os detalhes devem ter no máximo 500 caracteres.")
    return details or None


def normalize_uuid(value: str, label: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError) as exc:
        raise CommunityInputError(f"{label} inválido.") from exc


def contact_data_flags(value: str) -> list[str]:
    body = normalize_post_body(value)
    flags: list[str] = []
    if re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", body, re.IGNORECASE):
        flags.append("email")
    if re.search(r"\b(?:https?://|www\.)\S+", body, re.IGNORECASE):
        flags.append("link")
    if re.search(r"(?<!\d)(?:\+?\d[\s().-]*){7,}(?!\d)", body):
        flags.append("phone")
    return flags


def public_post(record: object) -> dict[str, object]:
    if not isinstance(record, dict):
        raise CommunityServiceError("A comunidade devolveu uma resposta inválida.")
    try:
        post_id = normalize_uuid(record.get("id"), "Publicação")
        pseudonym = str(record.get("pseudonym", "")).strip()
        body = normalize_post_body(record.get("body", ""))
        created_at = str(record.get("created_at", "")).strip()
        parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except (AttributeError, CommunityInputError, TypeError, ValueError) as exc:
        raise CommunityServiceError("A comunidade devolveu uma publicação inválida.") from exc
    if not re.fullmatch(r"Guerreiro\d{4}", pseudonym):
        raise CommunityServiceError("A comunidade devolveu uma publicação inválida.")
    if parsed_created_at.tzinfo is None:
        raise CommunityServiceError("A comunidade devolveu uma publicação inválida.")
    return {
        "id": post_id,
        "pseudonym": pseudonym,
        "body": body,
        "created_at": created_at,
    }


class SupabaseCommunity:
    REPORT_REASONS = {"personal_data", "harassment", "unsafe", "spam", "other"}
    MODERATION_STATUSES = {"published", "hidden", "rejected"}

    def __init__(self, config: CommunityConfig) -> None:
        config.validate()
        self.config = config

    def create_pending_post(self, user_id: str, body: str) -> dict[str, object]:
        normalized_user_id = normalize_uuid(user_id, "Utilizador")
        pseudonym = f"Guerreiro{secrets.randbelow(9000) + 1000}"
        record = self._request(
            "POST",
            "/rest/v1/rpc/submit_anonymous_post",
            payload={
                "p_user_id": normalized_user_id,
                "p_pseudonym": pseudonym,
                "p_body": normalize_post_body(body),
                "p_limit": self.config.daily_post_limit,
            },
        )
        if not isinstance(record, list):
            raise CommunityServiceError("A comunidade devolveu uma resposta inválida.")
        if not record:
            raise CommunityLimitError("O limite diário de partilhas foi atingido.")
        return public_post(record[0]) | {"status": "pending"}

    def list_published_posts(self, limit: int = 20) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, 50))
        records = self._request(
            "GET",
            "/rest/v1/anonymous_posts"
            f"?select=id,pseudonym,body,created_at&status=eq.published"
            f"&order=created_at.desc&limit={safe_limit}",
        )
        if not isinstance(records, list):
            raise CommunityServiceError("A comunidade devolveu uma resposta inválida.")
        published: list[dict[str, object]] = []
        for record in records:
            try:
                published.append(public_post(record))
            except CommunityServiceError:
                continue
        return published

    def report_post(
        self,
        user_id: str,
        post_id: str,
        reason: str,
        details: str | None = None,
    ) -> dict[str, object]:
        normalized_post_id = normalize_uuid(post_id, "Publicação")
        normalized_reason = reason.strip().lower()
        if normalized_reason not in self.REPORT_REASONS:
            raise CommunityInputError("Motivo de denúncia inválido.")
        visible = self._request(
            "GET",
            "/rest/v1/anonymous_posts"
            f"?select=id&id=eq.{quote(normalized_post_id, safe='')}&status=eq.published&limit=1",
        )
        if not isinstance(visible, list) or not visible:
            raise CommunityInputError("A publicação já não está disponível.")
        record = self._request(
            "POST",
            "/rest/v1/anonymous_reports",
            payload={
                "post_id": normalized_post_id,
                "reporter_id": normalize_uuid(user_id, "Utilizador"),
                "reason": normalized_reason,
                "details": normalize_details(details),
            },
            prefer="return=representation",
        )
        if not isinstance(record, list) or not record:
            raise CommunityServiceError("A denúncia não foi confirmada.")
        return {"reported": True}

    def list_pending_posts(self, limit: int = 50) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, 100))
        records = self._request(
            "GET",
            "/rest/v1/anonymous_posts"
            f"?select=id,pseudonym,body,status,created_at&status=eq.pending"
            f"&order=created_at.asc&limit={safe_limit}",
        )
        if not isinstance(records, list):
            raise CommunityServiceError("A fila de moderação devolveu uma resposta inválida.")
        pending: list[dict[str, object]] = []
        for record in records:
            try:
                item = public_post(record)
            except CommunityServiceError:
                continue
            if record.get("status") != "pending":
                continue
            pending.append(
                item
                | {
                    "status": "pending",
                    "review_flags": contact_data_flags(str(item["body"])),
                }
            )
        return pending

    def moderate_post(self, post_id: str, status: str, note: str | None = None) -> dict[str, object]:
        normalized_status = status.strip().lower()
        if normalized_status not in self.MODERATION_STATUSES:
            raise CommunityInputError("Decisão de moderação inválida.")
        normalized_post_id = normalize_uuid(post_id, "Publicação")
        if normalized_status == "published":
            current = self._request(
                "GET",
                "/rest/v1/anonymous_posts"
                f"?select=id,pseudonym,body,created_at,status&id=eq.{quote(normalized_post_id, safe='')}"
                "&status=eq.pending&limit=1",
            )
            if not isinstance(current, list) or not current:
                raise CommunityInputError("O estado atual da publicação já não permite esta decisão.")
            candidate = public_post(current[0])
            if contact_data_flags(str(candidate["body"])):
                raise CommunityInputError(
                    "A publicação contém possíveis contactos ou ligações e não pode ser publicada."
                )
        allowed_current_status = (
            "status=in.(pending,published)"
            if normalized_status == "hidden"
            else "status=eq.pending"
        )
        record = self._request(
            "PATCH",
            "/rest/v1/anonymous_posts"
            f"?id=eq.{quote(normalized_post_id, safe='')}"
            f"&{allowed_current_status}",
            payload={
                "status": normalized_status,
                "moderated_at": datetime.now(timezone.utc).isoformat(),
                "moderation_note": normalize_details(note),
            },
            prefer="return=representation",
        )
        if not isinstance(record, list) or not record:
            raise CommunityInputError("O estado atual da publicação já não permite esta decisão.")
        return public_post(record[0]) | {"status": record[0].get("status", normalized_status)}

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, object] | None = None,
        prefer: str | None = None,
    ) -> object:
        headers = {
            "apikey": self.config.service_role_key,
            "Authorization": f"Bearer {self.config.service_role_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        request = Request(
            f"{self.config.supabase_url}{path}",
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            method=method,
            headers=headers,
        )
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
        except HTTPError as exc:
            if exc.code == 409:
                raise CommunityConflictError("Esta denúncia já foi registada.") from exc
            raise CommunityServiceError(f"Supabase respondeu com HTTP {exc.code}") from exc
        except OSError as exc:
            raise CommunityServiceError("Não foi possível contactar a comunidade.") from exc
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise CommunityServiceError("A comunidade devolveu uma resposta inválida.") from exc
