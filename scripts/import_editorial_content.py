from __future__ import annotations

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

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
PUBLIC_DIR = ROOT / "public"
PLATFORM_HOSTS = {"soporhoje.cv", "www.soporhoje.cv"}


class IdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element_id = dict(attrs).get("id")
        if element_id:
            self.ids.add(element_id)


class DraftCatalog(Protocol):
    def list_for_review(self, limit: int = 200) -> list[dict[str, object]]: ...

    def create_draft(self, payload: dict[str, object]) -> dict[str, object]: ...

    def update_draft(self, item_id: str, payload: dict[str, object]) -> dict[str, object]: ...


def content_key(item: dict[str, object]) -> tuple[str, str]:
    return tuple(str(item.get(field) or "").strip().casefold() for field in ("kind", "title"))


def validate_internal_links(drafts: list[dict[str, object]], public_dir: Path = PUBLIC_DIR) -> None:
    public_root = public_dir.resolve()
    for item in drafts:
        parsed = urlparse(str(item.get("url") or ""))
        if parsed.hostname not in PLATFORM_HOSTS:
            continue
        relative = parsed.path.strip("/")
        target = (public_root / relative).resolve() if relative else public_root
        if target.is_dir():
            target = (target / "index.html").resolve()
        if not target.is_file() or not target.is_relative_to(public_root):
            raise ValueError(f"Ligação interna inexistente: {item['url']}")
        if parsed.fragment:
            parser = IdParser()
            parser.feed(target.read_text(encoding="utf-8"))
            if parsed.fragment not in parser.ids:
                raise ValueError(f"Âncora interna inexistente: {item['url']}")


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
    validate_internal_links(drafts)
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
