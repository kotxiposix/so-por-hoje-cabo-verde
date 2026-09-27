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

from sph.help_directory import (  # noqa: E402
    HelpDirectoryConfig,
    SupabaseHelpDirectory,
    normalize_resource,
)


DEFAULT_DATA_PATH = ROOT / "data" / "help_resources_drafts.json"


class DraftDirectory(Protocol):
    def list_for_review(self, limit: int = 200) -> list[dict[str, object]]: ...

    def create_draft(self, payload: dict[str, object]) -> dict[str, object]: ...

    def update_draft(self, resource_id: str, payload: dict[str, object]) -> dict[str, object]: ...


def resource_key(resource: dict[str, object]) -> tuple[str, str, str, str]:
    return tuple(
        str(resource.get(field) or "").strip().casefold()
        for field in ("name", "island", "municipality", "category")
    )


def load_drafts(path: Path) -> list[dict[str, object]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("O catálogo de recursos deve ser uma lista JSON.")
    drafts = [normalize_resource(item) for item in raw if isinstance(item, dict)]
    if len(drafts) != len(raw):
        raise ValueError("Todos os recursos devem ser objetos JSON.")
    keys = [resource_key(item) for item in drafts]
    if len(keys) != len(set(keys)):
        raise ValueError("O catálogo contém recursos duplicados.")
    return drafts


def apply_drafts(directory: DraftDirectory, drafts: list[dict[str, object]]) -> tuple[int, int]:
    existing = {
        resource_key(resource): resource
        for resource in directory.list_for_review(500)
        if isinstance(resource, dict)
    }
    created = 0
    updated = 0
    for draft in drafts:
        current = existing.get(resource_key(draft))
        resource_id = str(current.get("id") or "") if current else ""
        if resource_id:
            directory.update_draft(resource_id, draft)
            updated += 1
        else:
            directory.create_draft(draft)
            created += 1
    return created, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida ou importa recursos de ajuda como rascunhos.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--apply", action="store_true", help="Criar ou atualizar rascunhos no Supabase.")
    args = parser.parse_args()

    drafts = load_drafts(args.data)
    if not args.apply:
        print(f"Catálogo válido: {len(drafts)} recursos. Usa --apply para importar como rascunhos.")
        return 0

    directory = SupabaseHelpDirectory(HelpDirectoryConfig.from_environment())
    created, updated = apply_drafts(directory, drafts)
    print(f"Importação concluída: {created} criados, {updated} atualizados, todos em rascunho.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
