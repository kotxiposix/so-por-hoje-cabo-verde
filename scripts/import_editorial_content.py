from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sph.editorial_catalog import (  # noqa: E402
    EditorialConfig,
    SupabaseEditorialCatalog,
    normalize_item,
)


DEFAULT_DATA_PATH = ROOT / "data" / "editorial_content_drafts.json"


class DraftCatalog(Protocol):
    def list_for_review(self, limit: int = 200) -> list[dict[str, object]]: ...

    def create_draft(self, payload: dict[str, object]) -> dict[str, object]: ...

    def update_draft(self, item_id: str, payload: dict[str, object]) -> dict[str, object]: ...


def content_key(item: dict[str, object]) -> tuple[str, str]:
    return tuple(str(item.get(field) or "").strip().casefold() for field in ("kind", "title"))


def load_drafts(path: Path) -> list[dict[str, object]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("O catálogo editorial deve ser uma lista JSON.")
    drafts = [normalize_item(item) for item in raw if isinstance(item, dict)]
    if len(drafts) != len(raw):
        raise ValueError("Todos os conteúdos devem ser objetos JSON.")
    keys = [content_key(item) for item in drafts]
    if len(keys) != len(set(keys)):
        raise ValueError("O catálogo contém conteúdos duplicados.")
    return drafts


def apply_drafts(catalog: DraftCatalog, drafts: list[dict[str, object]]) -> tuple[int, int]:
    existing = {
        content_key(item): item
        for item in catalog.list_for_review(500)
        if isinstance(item, dict)
    }
    created = 0
    updated = 0
    for draft in drafts:
        current = existing.get(content_key(draft))
        item_id = str(current.get("id") or "") if current else ""
        if item_id:
            catalog.update_draft(item_id, draft)
            updated += 1
        else:
            catalog.create_draft(draft)
            created += 1
    return created, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida ou importa conteúdos editoriais como rascunhos.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--apply", action="store_true", help="Criar ou atualizar rascunhos no Supabase.")
    args = parser.parse_args()

    drafts = load_drafts(args.data)
    if not args.apply:
        print(f"Catálogo válido: {len(drafts)} conteúdos. Usa --apply para importar como rascunhos.")
        return 0

    catalog = SupabaseEditorialCatalog(EditorialConfig.from_environment())
    created, updated = apply_drafts(catalog, drafts)
    print(f"Importação concluída: {created} criados, {updated} atualizados, todos em rascunho.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
