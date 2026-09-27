from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from sph.editorial_catalog import (
    EditorialConfig,
    EditorialInputError,
    EditorialServiceError,
    SupabaseEditorialCatalog,
    normalize_item,
    public_item,
)


ITEM_ID = "4948b21e-facf-4bc8-a60e-8800b488dfee"
EDITOR_ID = "7d40d2bb-6202-4e1f-9231-724d15fc8e02"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "supabase" / "schema.sql"


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def config(enabled: bool = True) -> EditorialConfig:
    return EditorialConfig(enabled, "https://project.supabase.co", "service-role")


def payload() -> dict[str, object]:
    return {
        "kind": "podcast",
        "title": "Conversa sobre recuperação",
        "summary": "Uma conversa honesta sobre apoio, escolhas e recomeços.",
        "url": "https://example.cv/podcast",
        "image_url": "https://example.cv/capa.jpg",
        "display_date": "Setembro de 2026",
        "sort_order": 10,
    }


class EditorialCatalogTests(unittest.TestCase):
    def test_catalog_is_closed_until_explicitly_enabled(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        }
        with patch.dict(os.environ, environment, clear=True):
            self.assertFalse(EditorialConfig.from_environment().ready)
        with patch.dict(os.environ, {**environment, "EDITORIAL_CONTENT_READY": "true"}, clear=True):
            self.assertTrue(EditorialConfig.from_environment().ready)

    def test_drafts_can_be_managed_while_public_catalog_is_closed(self) -> None:
        catalog = SupabaseEditorialCatalog(config(False))
        with self.assertRaises(EditorialServiceError):
            catalog.list_published()

        returned = [{**payload(), "id": ITEM_ID, "status": "draft"}]
        with patch("sph.editorial_catalog.urlopen", return_value=FakeResponse(returned)):
            created = catalog.create_draft(payload(), actor_id=EDITOR_ID)

        self.assertEqual(created["status"], "draft")

    def test_validation_rejects_unknown_types_urls_and_orders(self) -> None:
        with self.assertRaises(EditorialInputError):
            normalize_item({**payload(), "kind": "unknown"})
        with self.assertRaises(EditorialInputError):
            normalize_item({**payload(), "url": "javascript:alert(1)"})
        with self.assertRaises(EditorialInputError):
            normalize_item({**payload(), "sort_order": 1000})
        with self.assertRaises(EditorialInputError):
            normalize_item({**payload(), "sort_order": True})

    def test_public_shape_excludes_status_authorship_and_sorting(self) -> None:
        visible = public_item({
            **payload(),
            "id": ITEM_ID,
            "status": "published",
            "last_edited_by": EDITOR_ID,
            "moderation_note": "private",
        })

        self.assertEqual(visible["id"], ITEM_ID)
        self.assertNotIn("status", visible)
        self.assertNotIn("last_edited_by", visible)
        self.assertNotIn("sort_order", visible)

    def test_public_listing_selects_only_published_items(self) -> None:
        returned = [{**payload(), "id": ITEM_ID}]
        with patch("sph.editorial_catalog.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            result = SupabaseEditorialCatalog(config()).list_published(999)

        request = urlopen_mock.call_args.args[0]
        self.assertIn("status=eq.published", request.full_url)
        self.assertIn("limit=100", request.full_url)
        self.assertNotIn("select=*", request.full_url)
        self.assertEqual(result[0]["id"], ITEM_ID)

    def test_draft_and_publish_transitions_capture_editor(self) -> None:
        returned = [{**payload(), "id": ITEM_ID, "status": "draft"}]
        with patch("sph.editorial_catalog.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            SupabaseEditorialCatalog(config()).create_draft(payload(), actor_id=EDITOR_ID)
        draft_payload = json.loads(urlopen_mock.call_args.args[0].data)
        self.assertEqual(draft_payload["status"], "draft")
        self.assertEqual(draft_payload["last_edited_by"], EDITOR_ID)

        published = [{**payload(), "id": ITEM_ID, "status": "published"}]
        responses = [FakeResponse(returned), FakeResponse(published)]
        with patch("sph.editorial_catalog.urlopen", side_effect=responses) as publish_mock:
            SupabaseEditorialCatalog(config()).publish(ITEM_ID, actor_id=EDITOR_ID)
        publish_payload = json.loads(publish_mock.call_args.args[0].data)
        self.assertEqual(publish_payload["status"], "published")
        self.assertEqual(publish_payload["last_edited_by"], EDITOR_ID)

    def test_schema_has_private_editorial_table_and_atomic_audit(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")

        self.assertIn("create table if not exists public.editorial_content", schema)
        self.assertIn("alter table public.editorial_content enable row level security", schema)
        self.assertIn('drop policy if exists "Public reads editorial content"', schema)
        self.assertNotIn('create policy "Public reads editorial content"', schema)
        self.assertIn("create trigger editorial_content_audit_trigger", schema)
        self.assertIn("'content.published'", schema)


if __name__ == "__main__":
    unittest.main()
