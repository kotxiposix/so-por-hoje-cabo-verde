from __future__ import annotations

import json
import os
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
    def ready(self) -> bool:
        return bool(self.enabled and self.supabase_url and self.service_role_key)

    def validate(self) -> None:
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
    if cleaned and not cleaned.lower().startswith(("https://", "http://")):
        raise HelpDirectoryInputError(f"{label} deve começar por https:// ou http://.")
    return cleaned


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
        "phone": clean_text(payload.get("phone"), "Telefone", 80),
        "email": clean_text(payload.get("email"), "Email", 254),
        "website": clean_url(payload.get("website"), "Website"),
        "schedule": schedule,
        "is_emergency": bool(payload.get("is_emergency", False)),
        "source_url": clean_url(payload.get("source_url"), "Fonte"),
    }


def public_resource(record: object) -> dict[str, object]:
    if not isinstance(record, dict):
        raise HelpDirectoryServiceError("O diretório devolveu uma resposta inválida.")
    return {key: record[key] for key in PUBLIC_FIELDS if key in record}


class SupabaseHelpDirectory:
    def __init__(self, config: HelpDirectoryConfig) -> None:
        config.validate()
        self.config = config

    def list_verified(self, limit: int = 100) -> list[dict[str, object]]:
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
        return [public_resource(record) for record in records]

    def list_for_review(self, limit: int = 200) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, 500))
        records = self._request(
            "GET",
            f"/rest/v1/help_resources?select=*&order=updated_at.desc&limit={safe_limit}",
        )
        if not isinstance(records, list):
            raise HelpDirectoryServiceError("O diretório devolveu uma resposta inválida.")
        return records

    def create_draft(self, payload: dict[str, object]) -> dict[str, object]:
        record = self._request(
            "POST",
            "/rest/v1/help_resources",
            payload=self._as_draft(normalize_resource(payload)),
            prefer="return=representation",
        )
        return self._one(record, "O recurso não foi criado.")

    def update_draft(self, resource_id: str, payload: dict[str, object]) -> dict[str, object]:
        record = self._request(
            "PATCH",
            f"/rest/v1/help_resources?id=eq.{quote(normalize_uuid(resource_id), safe='')}",
            payload=self._as_draft(normalize_resource(payload)),
            prefer="return=representation",
        )
        return self._one(record, "O recurso não foi encontrado.")

    def verify(self, resource_id: str, review_days: int) -> dict[str, object]:
        safe_days = max(1, min(review_days, 365))
        now = datetime.now(timezone.utc)
        record = self._request(
            "PATCH",
            "/rest/v1/help_resources"
            f"?id=eq.{quote(normalize_uuid(resource_id), safe='')}&source_url=not.is.null",
            payload={
                "is_verified": True,
                "verification_status": "verified",
                "verified_at": now.isoformat(),
                "review_due_at": (now.date() + timedelta(days=safe_days)).isoformat(),
                "updated_at": now.isoformat(),
            },
            prefer="return=representation",
        )
        return self._one(record, "O recurso precisa de uma fonte antes da verificação.")

    def retire(self, resource_id: str) -> dict[str, object]:
        now = datetime.now(timezone.utc).isoformat()
        record = self._request(
            "PATCH",
            f"/rest/v1/help_resources?id=eq.{quote(normalize_uuid(resource_id), safe='')}",
            payload={
                "is_verified": False,
                "verification_status": "retired",
                "review_due_at": None,
                "updated_at": now,
            },
            prefer="return=representation",
        )
        return self._one(record, "O recurso não foi encontrado.")

    @staticmethod
    def _as_draft(payload: dict[str, object]) -> dict[str, object]:
        return payload | {
            "is_verified": False,
            "verification_status": "draft",
            "verified_at": None,
            "review_due_at": None,
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
