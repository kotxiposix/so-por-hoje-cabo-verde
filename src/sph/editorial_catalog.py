from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID


class EditorialInputError(ValueError):
    pass


class EditorialServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class EditorialConfig:
    enabled: bool
    supabase_url: str
    service_role_key: str

    @classmethod
    def from_environment(cls) -> "EditorialConfig":
        return cls(
            enabled=os.getenv("EDITORIAL_CONTENT_READY", "").strip().lower() in {"1", "true", "yes"},
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
            raise EditorialServiceError("A gestão editorial ainda não está configurada.")

    def validate_public(self) -> None:
        if not self.ready:
            raise EditorialServiceError("O catálogo editorial ainda não está ativo.")


PUBLIC_FIELDS = (
    "id",
    "kind",
    "title",
    "summary",
    "url",
    "image_url",
    "display_date",
)
ALLOWED_KINDS = {"podcast", "video", "story", "resource", "exhibition", "event"}


def clean_text(value: object, label: str, max_length: int, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise EditorialInputError(f"{label} é obrigatório.")
        return None
    cleaned = " ".join(str(value).split())
    if required and not cleaned:
        raise EditorialInputError(f"{label} é obrigatório.")
    if len(cleaned) > max_length:
        raise EditorialInputError(f"{label} excede {max_length} caracteres.")
    return cleaned or None


def clean_url(value: object, label: str, *, required: bool = False) -> str | None:
    cleaned = clean_text(value, label, 500, required=required)
    if cleaned and not cleaned.lower().startswith("https://"):
        raise EditorialInputError(f"{label} deve começar por https://.")
    return cleaned


def normalize_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError) as exc:
        raise EditorialInputError("Conteúdo editorial inválido.") from exc


def normalize_item(payload: dict[str, object]) -> dict[str, object]:
    kind = clean_text(payload.get("kind"), "Tipo", 30, required=True)
    if kind not in ALLOWED_KINDS:
        raise EditorialInputError("Tipo editorial inválido.")
    sort_order = payload.get("sort_order", 0)
    if not isinstance(sort_order, int) or isinstance(sort_order, bool) or not -999 <= sort_order <= 999:
        raise EditorialInputError("Ordem editorial inválida.")
    display_date = clean_text(payload.get("display_date"), "Data apresentada", 80)
    return {
        "kind": kind,
        "title": clean_text(payload.get("title"), "Título", 160, required=True),
        "summary": clean_text(payload.get("summary"), "Resumo", 600, required=True),
        "url": clean_url(payload.get("url"), "Ligação"),
        "image_url": clean_url(payload.get("image_url"), "Imagem"),
        "display_date": display_date,
        "sort_order": sort_order,
    }


def validate_publishable_item(record: dict[str, object]) -> dict[str, object]:
    normalized = normalize_item(record)
    if not normalized["url"]:
        raise EditorialInputError("O conteúdo precisa de uma ligação HTTPS antes da publicação.")
    return normalized


def public_item(record: object) -> dict[str, object]:
    if not isinstance(record, dict):
        raise EditorialServiceError("O catálogo editorial devolveu uma resposta inválida.")
    normalized = normalize_item(record)
    visible = {"id": normalize_uuid(str(record.get("id") or "")), **normalized}
    return {key: visible[key] for key in PUBLIC_FIELDS}


class SupabaseEditorialCatalog:
    def __init__(self, config: EditorialConfig) -> None:
        config.validate()
        self.config = config

    def list_published(self, limit: int = 50) -> list[dict[str, object]]:
        self.config.validate_public()
        safe_limit = max(1, min(limit, 100))
        fields = ",".join(PUBLIC_FIELDS) + ",sort_order"
        records = self._request(
            "GET",
            "/rest/v1/editorial_content"
            f"?select={fields}&status=eq.published"
            f"&order=sort_order.asc,published_at.desc&limit={safe_limit}",
        )
        if not isinstance(records, list):
            raise EditorialServiceError("O catálogo editorial devolveu uma resposta inválida.")
        visible: list[dict[str, object]] = []
        for record in records:
            try:
                visible.append(public_item(record))
            except (EditorialInputError, EditorialServiceError):
                continue
        return visible

    def list_for_review(self, limit: int = 200) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, 500))
        records = self._request(
            "GET",
            f"/rest/v1/editorial_content?select=*&order=updated_at.desc&limit={safe_limit}",
        )
        if not isinstance(records, list):
            raise EditorialServiceError("O catálogo editorial devolveu uma resposta inválida.")
        return records

    def create_draft(self, payload: dict[str, object], *, actor_id: str | None = None) -> dict[str, object]:
        record = self._request(
            "POST",
            "/rest/v1/editorial_content",
            payload=self._as_draft(normalize_item(payload), actor_id),
            prefer="return=representation",
        )
        return self._one(record, "O conteúdo não foi criado.")

    def update_draft(
        self,
        item_id: str,
        payload: dict[str, object],
        *,
        actor_id: str | None = None,
    ) -> dict[str, object]:
        record = self._request(
            "PATCH",
            f"/rest/v1/editorial_content?id=eq.{quote(normalize_uuid(item_id), safe='')}",
            payload=self._as_draft(normalize_item(payload), actor_id),
            prefer="return=representation",
        )
        return self._one(record, "O conteúdo não foi encontrado.")

    def publish(self, item_id: str, *, actor_id: str) -> dict[str, object]:
        normalized_id = quote(normalize_uuid(item_id), safe="")
        existing = self._request(
            "GET",
            f"/rest/v1/editorial_content?select=*&id=eq.{normalized_id}&limit=1",
        )
        validate_publishable_item(self._one(existing, "O conteúdo não foi encontrado."))
        record = self._request(
            "PATCH",
            f"/rest/v1/editorial_content?id=eq.{normalized_id}",
            payload={
                "status": "published",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "last_edited_by": normalize_uuid(actor_id),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            prefer="return=representation",
        )
        return self._one(record, "O conteúdo não foi encontrado.")

    def retire(self, item_id: str, *, actor_id: str) -> dict[str, object]:
        record = self._request(
            "PATCH",
            f"/rest/v1/editorial_content?id=eq.{quote(normalize_uuid(item_id), safe='')}",
            payload={
                "status": "retired",
                "last_edited_by": normalize_uuid(actor_id),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            prefer="return=representation",
        )
        return self._one(record, "O conteúdo não foi encontrado.")

    @staticmethod
    def _as_draft(payload: dict[str, object], actor_id: str | None) -> dict[str, object]:
        return {
            **payload,
            "status": "draft",
            "published_at": None,
            "last_edited_by": normalize_uuid(actor_id) if actor_id else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _one(value: object, message: str) -> dict[str, object]:
        if not isinstance(value, list) or not value or not isinstance(value[0], dict):
            raise EditorialServiceError(message)
        return value[0]

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
            method=method,
            headers=headers,
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        )
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
        except HTTPError as exc:
            raise EditorialServiceError(f"Supabase respondeu com HTTP {exc.code}") from exc
        except OSError as exc:
            raise EditorialServiceError("Não foi possível consultar o catálogo editorial.") from exc
        try:
            return json.loads(raw) if raw else []
        except json.JSONDecodeError as exc:
            raise EditorialServiceError("O catálogo editorial devolveu uma resposta inválida.") from exc
