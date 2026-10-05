from __future__ import annotations

import json
from datetime import datetime
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID

from sph.staff_access import StaffAccessConfig
from sph.security import supabase_headers


class StaffAuditServiceError(RuntimeError):
    pass


ALLOWED_ACTIONS = {
    "community.published",
    "community.hidden",
    "community.rejected",
    "help.created",
    "help.updated",
    "help.verified",
    "help.retired",
    "help.stale",
    "content.created",
    "content.updated",
    "content.published",
    "content.retired",
    "staff_role.admin.activated",
    "staff_role.admin.suspended",
    "staff_role.moderator.activated",
    "staff_role.moderator.suspended",
    "staff_role.help_editor.activated",
    "staff_role.help_editor.suspended",
    "staff_role.content_editor.activated",
    "staff_role.content_editor.suspended",
}
ALLOWED_TARGETS = {"community_post", "help_resource", "editorial_content", "staff_role"}


def short_reference(value: object, prefix: str) -> str:
    try:
        normalized = str(UUID(str(value)))
    except (TypeError, ValueError) as exc:
        raise StaffAuditServiceError("A auditoria devolveu um identificador inválido.") from exc
    return f"{prefix} …{normalized[-6:]}"


def public_audit_event(record: object) -> dict[str, str]:
    if not isinstance(record, dict):
        raise StaffAuditServiceError("A auditoria devolveu uma resposta inválida.")
    action = str(record.get("action") or "")
    target_type = str(record.get("target_type") or "")
    created_at = str(record.get("created_at") or "")
    if action not in ALLOWED_ACTIONS or target_type not in ALLOWED_TARGETS:
        raise StaffAuditServiceError("A auditoria devolveu um evento inválido.")
    try:
        parsed_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StaffAuditServiceError("A auditoria devolveu uma data inválida.") from exc
    if parsed_at.tzinfo is None:
        raise StaffAuditServiceError("A auditoria devolveu uma data inválida.")
    actor_id = record.get("actor_id")
    actor_ref = "Conta removida" if actor_id is None else short_reference(actor_id, "Conta")
    target_prefix = "Conta" if target_type == "staff_role" else "Item"
    return {
        "action": action,
        "target_type": target_type,
        "target_ref": short_reference(record.get("target_id"), target_prefix),
        "actor_ref": actor_ref,
        "created_at": created_at,
    }


class SupabaseStaffAudit:
    def __init__(self, config: StaffAccessConfig) -> None:
        config.validate()
        self.config = config

    def list_events(self, limit: int = 100) -> list[dict[str, str]]:
        safe_limit = max(1, min(limit, 200))
        fields = "action,target_type,target_id,actor_id,created_at"
        request = Request(
            f"{self.config.supabase_url}/rest/v1/staff_audit_events"
            f"?select={quote(fields, safe=',')}&order=created_at.desc,id.desc&limit={safe_limit}",
            method="GET",
            headers=supabase_headers(self.config.service_role_key),
        )
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
        except HTTPError as exc:
            raise StaffAuditServiceError(f"Supabase respondeu com HTTP {exc.code}") from exc
        except OSError as exc:
            raise StaffAuditServiceError("Não foi possível consultar a auditoria.") from exc
        try:
            records = json.loads(raw) if raw else []
        except json.JSONDecodeError as exc:
            raise StaffAuditServiceError("A auditoria devolveu uma resposta inválida.") from exc
        if not isinstance(records, list):
            raise StaffAuditServiceError("A auditoria devolveu uma resposta inválida.")
        events: list[dict[str, str]] = []
        for record in records:
            try:
                events.append(public_audit_event(record))
            except StaffAuditServiceError:
                continue
        return events
