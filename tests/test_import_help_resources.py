from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "import_help_resources.py"
SPEC = importlib.util.spec_from_file_location("import_help_resources", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeDirectory:
    def __init__(self) -> None:
        self.created: list[dict[str, object]] = []
        self.updated: list[tuple[str, dict[str, object]]] = []

    def list_for_review(self, limit: int = 200) -> list[dict[str, object]]:
        self.limit = limit
        return [{
            "id": "4948b21e-facf-4bc8-a60e-8800b488dfee",
            "name": "CCAD",
            "island": "Santiago",
            "municipality": "Praia",
            "category": "information",
        }]

    def create_draft(self, payload: dict[str, object]) -> dict[str, object]:
        self.created.append(payload)
        return payload

    def update_draft(self, resource_id: str, payload: dict[str, object]) -> dict[str, object]:
        self.updated.append((resource_id, payload))
        return payload


class ImportHelpResourcesTests(unittest.TestCase):
    def test_catalog_is_valid_and_unique(self) -> None:
        drafts = MODULE.load_drafts(MODULE.DEFAULT_DATA_PATH)

        self.assertGreaterEqual(len(drafts), 15)
        self.assertEqual(len(drafts), len({MODULE.resource_key(item) for item in drafts}))
        self.assertTrue(all(item["name"] and item["category"] for item in drafts))

    def test_every_draft_has_a_visible_local_fallback(self) -> None:
        drafts = MODULE.load_drafts(MODULE.DEFAULT_DATA_PATH)
        index_text = (ROOT / "public" / "index.html").read_text(encoding="utf-8")

        for resource in drafts:
            display_name = str(resource["name"])
            if resource["category"] == "meeting" and display_name.startswith("Grupo "):
                display_name = display_name.removeprefix("Grupo ")
            with self.subTest(resource=resource["name"]):
                self.assertIn(display_name, index_text)

    def test_import_updates_matches_and_creates_missing_drafts(self) -> None:
        directory = FakeDirectory()
        drafts = [
            {
                "name": "CCAD",
                "island": "Santiago",
                "municipality": "Praia",
                "category": "information",
            },
            {
                "name": "Linha SOS Álcool",
                "island": None,
                "municipality": None,
                "category": "emergency",
            },
        ]

        created, updated = MODULE.apply_drafts(directory, drafts)

        self.assertEqual((created, updated), (1, 1))
        self.assertEqual(directory.limit, 500)
        self.assertEqual(directory.updated[0][0], "4948b21e-facf-4bc8-a60e-8800b488dfee")


if __name__ == "__main__":
    unittest.main()
