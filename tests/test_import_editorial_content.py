from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "import_editorial_content.py"
SPEC = importlib.util.spec_from_file_location("import_editorial_content", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeCatalog:
    def __init__(self) -> None:
        self.created: list[dict[str, object]] = []
        self.updated: list[tuple[str, dict[str, object]]] = []

    def list_for_review(self, limit: int = 200) -> list[dict[str, object]]:
        self.limit = limit
        return [{
            "id": "4948b21e-facf-4bc8-a60e-8800b488dfee",
            "kind": "podcast",
            "title": "Podcast Só Por Hoje Cabo Verde",
        }]

    def create_draft(self, payload: dict[str, object]) -> dict[str, object]:
        self.created.append(payload)
        return payload

    def update_draft(self, item_id: str, payload: dict[str, object]) -> dict[str, object]:
        self.updated.append((item_id, payload))
        return payload


class ImportEditorialContentTests(unittest.TestCase):
    def test_catalog_is_valid_unique_and_https_only(self) -> None:
        drafts = MODULE.load_drafts(MODULE.DEFAULT_DATA_PATH)

        self.assertGreaterEqual(len(drafts), 5)
        self.assertEqual(len(drafts), len({MODULE.content_key(item) for item in drafts}))
        self.assertTrue(all(str(item["url"]).startswith("https://") for item in drafts))

    def test_import_updates_matches_and_creates_missing_drafts(self) -> None:
        catalog = FakeCatalog()
        drafts = [
            {"kind": "podcast", "title": "Podcast Só Por Hoje Cabo Verde"},
            {"kind": "video", "title": "Investir na prevenção"},
        ]

        created, updated = MODULE.apply_drafts(catalog, drafts)

        self.assertEqual((created, updated), (1, 1))
        self.assertEqual(catalog.limit, 500)
        self.assertEqual(catalog.updated[0][0], "4948b21e-facf-4bc8-a60e-8800b488dfee")

    def test_catalog_internal_links_resolve_to_real_pages_and_anchors(self) -> None:
        drafts = MODULE.load_drafts(MODULE.DEFAULT_DATA_PATH)

        MODULE.validate_internal_links(drafts)
        author = next(item for item in drafts if item["kind"] == "story")
        self.assertEqual(author["url"], "https://soporhoje.cv/expo#autor")

    def test_catalog_rejects_a_missing_internal_anchor(self) -> None:
        drafts = json.loads(MODULE.DEFAULT_DATA_PATH.read_text(encoding="utf-8"))
        drafts[0]["url"] = "https://soporhoje.cv/expo#nao-existe"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "drafts.json"
            path.write_text(json.dumps(drafts, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Âncora interna inexistente"):
                MODULE.load_drafts(path)


if __name__ == "__main__":
    unittest.main()
