from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID
from zoneinfo import ZoneInfo


class HelpDirectoryInputError(ValueError):
    pass


class HelpDirectoryServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class HelpDirectoryConfig:
    enabled: bool
    supabase_url: str
    service_role_key: str

    @classmethod
    def from_environment(cls) -> "HelpDirectoryConfig":
        return cls(
            enabled=os.getenv("HELP_DIRECTORY_READY", "").strip().lower() in {"1", "true", "yes"},
            supabase_url=os.getenv("SUPABASE_URL", "").strip().rstrip("/"),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        )

    @property
    def management_ready(self) -> bool:
        return bool(self.supabase_url and self.service_role_key)

    @property
    def ready(self) -> bool:
        return bool(self.enabled and self.management_ready)

    def validate(self) -> None:
        if not self.management_ready:
            raise HelpDirectoryServiceError("A gestão do diretório ainda não está configurada.")

    def validate_public(self) -> None:
        if not self.ready:
            raise HelpDirectoryServiceError("O diretório verificado ainda não está ativo.")


PUBLIC_FIELDS = (
    "id",
    "name",
    "island",
    "municipality",
    "category",
    "description",
    "phone",
    "email",
    "website",
    "schedule",
    "is_emergency",
    "source_url",
    "verified_at",
    "review_due_at",
)


def clean_text(value: object, label: str, max_length: int, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise HelpDirectoryInputError(f"{label} é obrigatório.")
        return None
    cleaned = " ".join(str(value).split())
    if required and not cleaned:
        raise HelpDirectoryInputError(f"{label} é obrigatório.")
    if len(cleaned) > max_length:
        raise HelpDirectoryInputError(f"{label} excede {max_length} caracteres.")
    return cleaned or None


def clean_url(value: object, label: str) -> str | None:
    cleaned = clean_text(value, label, 500)
    if cleaned and not cleaned.lower().startswith("https://"):
        raise HelpDirectoryInputError(f"{label} deve começar por https://.")
    return cleaned


def clean_email(value: object) -> str | None:
    cleaned = clean_text(value, "Email", 254)
    if cleaned and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", cleaned):
        raise HelpDirectoryInputError("Email inválido.")
    return cleaned


def clean_phone(value: object) -> str | None:
    cleaned = clean_text(value, "Telefone", 80)
    if cleaned and len(re.sub(r"\D", "", cleaned)) < 6:
        raise HelpDirectoryInputError("Telefone inválido.")
    return cleaned


def clean_boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise HelpDirectoryInputError(f"{label} deve ser verdadeiro ou falso.")
    return value


def normalize_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError) as exc:
        raise HelpDirectoryInputError("Recurso inválido.") from exc


def normalize_resource(payload: dict[str, object]) -> dict[str, object]:
    category = clean_text(payload.get("category"), "Categoria", 40, required=True)
    allowed_categories = {
        "emergency",
        "health",
        "treatment",
        "meeting",
        "family",
        "information",
        "other",
    }
    if category not in allowed_categories:
        raise HelpDirectoryInputError("Categoria inválida.")

    raw_schedule = payload.get("schedule", [])
    if not isinstance(raw_schedule, list) or len(raw_schedule) > 20:
        raise HelpDirectoryInputError("Horário inválido.")
    schedule: list[str] = []
    for item in raw_schedule:
        cleaned = clean_text(item, "Horário", 120, required=True)
        if cleaned:
            schedule.append(cleaned)

    return {
        "name": clean_text(payload.get("name"), "Nome", 120, required=True),
        "island": clean_text(payload.get("island"), "Ilha", 60),
        "municipality": clean_text(payload.get("municipality"), "Município", 80),
        "category": category,
        "description": clean_text(payload.get("description"), "Descrição", 1000),
        "phone": clean_phone(payload.get("phone")),
        "email": clean_email(payload.get("email")),
        "website": clean_url(payload.get("website"), "Website"),
        "schedule": schedule,
        "is_emergency": clean_boolean(payload.get("is_emergency", False), "Emergência"),
        "source_url": clean_url(payload.get("source_url"), "Fonte"),
    }


def public_resource(record: object) -> dict[str, object]:
    if not isinstance(record, dict):
        raise HelpDirectoryServiceError("O diretório devolveu uma resposta inválida.")
    normalized = normalize_resource(record)
    visible = {
        "id": normalize_uuid(str(record.get("id") or "")),
        **normalized,
        "verified_at": clean_text(record.get("verified_at"), "Data de verificação", 40),
        "review_due_at": clean_text(record.get("review_due_at"), "Prazo de revisão", 10),
    }
    return {key: visible[key] for key in PUBLIC_FIELDS if key in visible}


def validate_verifiable_resource(record: dict[str, object]) -> dict[str, object]:
    normalized = normalize_resource(record)
    if not normalized["source_url"]:
        raise HelpDirectoryInputError("O recurso precisa de uma fonte HTTPS antes da verificação.")
    if not normalized["description"]:
        raise HelpDirectoryInputError("O recurso precisa de uma descrição antes da verificação.")
    if normalized["is_emergency"] and not normalized["phone"]:
        raise HelpDirectoryInputError("Um recurso de emergência precisa de telefone confirmado.")
    if normalized["category"] in {"meeting", "family"}:
        if not normalized["schedule"]:
            raise HelpDirectoryInputError("Uma reunião precisa de horário confirmado.")
        if not any(normalized[field] for field in ("phone", "email", "website")):
            raise HelpDirectoryInputError("Uma reunião precisa de contacto confirmado.")
    return normalized


class SupabaseHelpDirectory:
    def __init__(self, config: HelpDirectoryConfig) -> None:
        config.validate()
        self.config = config

    def list_verified(self, limit: int = 100) -> list[dict[str, object]]:
        self.config.validate_public()
        safe_limit = max(1, min(limit, 200))
        today = datetime.now(ZoneInfo("Atlantic/Cape_Verde")).date().isoformat()
        fields = ",".join(PUBLIC_FIELDS)
        records = self._request(
            "GET",
            "/rest/v1/help_resources"
            f"?select={fields}&is_verified=eq.true&verification_status=eq.verified"
            f"&review_due_at=gte.{today}&order=is_emergency.desc,name.asc&limit={safe_limit}",
        )
        if not isinstance(records, list):
            raise HelpDirectoryServiceError("O diretório devolveu uma resposta inválida.")
        visible: list[dict[str, object]] = []
        for record in records:
            try:
                visible.append(public_resource(record))
            except (HelpDirectoryInputError, HelpDirectoryServiceError):
                continue
        return visible

    def list_for_review(self, limit: int = 200) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, 500))
        records = self._request(
            "GET",
            f"/rest/v1/help_resources?select=*&order=updated_at.desc&limit={safe_limit}",
        )
        if not isinstance(records, list):
            raise HelpDirectoryServiceError("O diretório devolveu uma resposta inválida.")
        return records

    def create_draft(
        self,
        payload: dict[str, object],
        *,
        actor_id: str | None = None,
    ) -> dict[str, object]:
        record = self._request(
            "POST",
            "/rest/v1/help_resources",
            payload=self._as_draft(normalize_resource(payload), actor_id),
            prefer="return=representation",
        )
        return self._one(record, "O recurso não foi criado.")

    def update_draft(
        self,
        resource_id: str,
        payload: dict[str, object],
        *,
        actor_id: str | None = None,
    ) -> dict[str, object]:
        record = self._request(
            "PATCH",
            f"/rest/v1/help_resources?id=eq.{quote(normalize_uuid(resource_id), safe='')}",
            payload=self._as_draft(normalize_resource(payload), actor_id),
            prefer="return=representation",
        )
        return self._one(record, "O recurso não foi encontrado.")

    def verify(
        self,
        resource_id: str,
        review_days: int,
        *,
        actor_id: str | None = None,
    ) -> dict[str, object]:
        safe_days = max(1, min(review_days, 365))
        now = datetime.now(timezone.utc)
        normalized_id = quote(normalize_uuid(resource_id), safe="")
        existing = self._request(
            "GET",
            f"/rest/v1/help_resources?select=*&id=eq.{normalized_id}&limit=1",
        )
        record_to_verify = self._one(existing, "O recurso não foi encontrado.")
        validate_verifiable_resource(record_to_verify)
        record = self._request(
            "PATCH",
            f"/rest/v1/help_resources?id=eq.{normalized_id}",
            payload={
                "is_verified": True,
                "verification_status": "verified",
                "verified_at": now.isoformat(),
                "review_due_at": (now.date() + timedelta(days=safe_days)).isoformat(),
                "last_edited_by": normalize_uuid(actor_id) if actor_id else None,
                "updated_at": now.isoformat(),
            },
            prefer="return=representation",
        )
        return self._one(record, "O recurso não foi encontrado.")

    def retire(self, resource_id: str, *, actor_id: str | None = None) -> dict[str, object]:
        now = datetime.now(timezone.utc).isoformat()
        record = self._request(
            "PATCH",
            f"/rest/v1/help_resources?id=eq.{quote(normalize_uuid(resource_id), safe='')}",
            payload={
                "is_verified": False,
                "verification_status": "retired",
                "review_due_at": None,
                "last_edited_by": normalize_uuid(actor_id) if actor_id else None,
                "updated_at": now,
            },
            prefer="return=representation",
        )
        return self._one(record, "O recurso não foi encontrado.")

    @staticmethod
    def _as_draft(payload: dict[str, object], actor_id: str | None = None) -> dict[str, object]:
        return payload | {
            "is_verified": False,
            "verification_status": "draft",
            "verified_at": None,
            "review_due_at": None,
            "last_edited_by": normalize_uuid(actor_id) if actor_id else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _one(record: object, message: str) -> dict[str, object]:
        if not isinstance(record, list):
            raise HelpDirectoryServiceError("O diretório devolveu uma resposta inválida.")
        if not record or not isinstance(record[0], dict):
            raise HelpDirectoryInputError(message)
        return record[0]

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
            raise HelpDirectoryServiceError(f"Supabase respondeu com HTTP {exc.code}") from exc
        except OSError as exc:
            raise HelpDirectoryServiceError("Não foi possível contactar o diretório.") from exc
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise HelpDirectoryServiceError("O diretório devolveu uma resposta inválida.") from exc
