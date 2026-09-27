from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from sph.community import (
    CommunityConfig,
    CommunityInputError,
    CommunityLimitError,
    SupabaseCommunity,
    contact_data_flags,
    normalize_post_body,
)


USER_ID = "7d40d2bb-6202-4e1f-9231-724d15fc8e02"
POST_ID = "7a0c9820-4e7a-40f6-a32b-6f5ce402ef68"
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


def config() -> CommunityConfig:
    return CommunityConfig(True, "https://project.supabase.co", "service-role", 3)


class CommunityTests(unittest.TestCase):
    def test_community_is_closed_until_explicitly_enabled(self) -> None:
        environment = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        }
        with patch.dict(os.environ, environment, clear=True):
            self.assertFalse(CommunityConfig.from_environment().ready)
        with patch.dict(os.environ, {**environment, "COMMUNITY_READY": "true"}, clear=True):
            self.assertTrue(CommunityConfig.from_environment().ready)

    def test_post_body_is_normalized_and_bounded(self) -> None:
        self.assertEqual(normalize_post_body("  Preciso\n de apoio. "), "Preciso de apoio.")
        with self.assertRaises(CommunityInputError):
            normalize_post_body(" ")
        with self.assertRaises(CommunityInputError):
            normalize_post_body("a" * 281)

    def test_contact_data_flags_are_limited_to_clear_signals(self) -> None:
        self.assertEqual(contact_data_flags("Hoje preciso de falar com alguém."), [])
        self.assertEqual(contact_data_flags("Escreve para pessoa@example.cv"), ["email"])
        self.assertEqual(contact_data_flags("Liga +238 999 12 34"), ["phone"])
        self.assertEqual(contact_data_flags("Vê https://example.cv/apoio"), ["link"])

    def test_pending_post_uses_server_pseudonym_and_hides_author(self) -> None:
        returned = [{
            "id": POST_ID,
            "author_id": USER_ID,
            "pseudonym": "Guerreiro1234",
            "body": "Um dia de cada vez.",
            "status": "pending",
            "created_at": "2026-09-26T12:00:00Z",
            "moderation_note": None,
        }]
        with patch("sph.community.secrets.randbelow", return_value=234), patch(
            "sph.community.urlopen", return_value=FakeResponse(returned)
        ) as urlopen_mock:
            result = SupabaseCommunity(config()).create_pending_post(USER_ID, "Um dia de cada vez.")

        request = urlopen_mock.call_args.args[0]
        self.assertIn("submit_anonymous_post", request.full_url)
        payload = json.loads(request.data)
        self.assertEqual(payload["p_pseudonym"], "Guerreiro1234")
        self.assertEqual(payload["p_user_id"], USER_ID)
        self.assertEqual(payload["p_limit"], 3)
        self.assertNotIn("author_id", result)
        self.assertNotIn("moderation_note", result)
        self.assertEqual(result["status"], "pending")

    def test_daily_post_limit_stops_before_inserting(self) -> None:
        with patch("sph.community.urlopen", return_value=FakeResponse([])) as urlopen_mock:
            with self.assertRaises(CommunityLimitError):
                SupabaseCommunity(config()).create_pending_post(USER_ID, "Mais uma partilha.")

        self.assertEqual(urlopen_mock.call_count, 1)

    def test_public_listing_selects_only_safe_fields(self) -> None:
        returned = [{
            "id": POST_ID,
            "pseudonym": "Guerreiro1234",
            "body": "Partilha publicada.",
            "created_at": "2026-09-26T12:00:00Z",
        }]
        with patch("sph.community.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            result = SupabaseCommunity(config()).list_published_posts(500)

        request = urlopen_mock.call_args.args[0]
        self.assertIn("select=id,pseudonym,body,created_at", request.full_url)
        self.assertIn("status=eq.published", request.full_url)
        self.assertIn("limit=50", request.full_url)
        self.assertEqual(result, returned)

    def test_public_listing_skips_malformed_database_records(self) -> None:
        returned = [
            {
                "id": POST_ID,
                "pseudonym": "Guerreiro1234",
                "body": "Partilha publicada.",
                "created_at": "2026-09-26T12:00:00Z",
            },
            {
                "id": "not-a-uuid",
                "pseudonym": "Nome real",
                "body": "a" * 281,
                "created_at": "ontem",
            },
        ]
        with patch("sph.community.urlopen", return_value=FakeResponse(returned)):
            result = SupabaseCommunity(config()).list_published_posts()

        self.assertEqual(result, [returned[0]])

    def test_publishing_requires_a_still_pending_post(self) -> None:
        returned = [{
            "id": POST_ID,
            "pseudonym": "Guerreiro1234",
            "body": "Partilha aprovada.",
            "status": "published",
            "created_at": "2026-09-26T12:00:00Z",
        }]
        responses = [FakeResponse(returned), FakeResponse(returned)]
        with patch("sph.community.urlopen", side_effect=responses) as urlopen_mock:
            result = SupabaseCommunity(config()).moderate_post(POST_ID, "published")

        self.assertIn("status=eq.pending", urlopen_mock.call_args_list[1].args[0].full_url)
        self.assertEqual(result["status"], "published")

    def test_publishing_blocks_clear_contact_data(self) -> None:
        returned = [{
            "id": POST_ID,
            "pseudonym": "Guerreiro1234",
            "body": "Liga para +238 999 12 34.",
            "status": "pending",
            "created_at": "2026-09-26T12:00:00Z",
        }]
        with patch("sph.community.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            with self.assertRaisesRegex(CommunityInputError, "possíveis contactos"):
                SupabaseCommunity(config()).moderate_post(POST_ID, "published")

        self.assertEqual(urlopen_mock.call_count, 1)

    def test_pending_queue_marks_contact_data_for_human_review(self) -> None:
        returned = [{
            "id": POST_ID,
            "pseudonym": "Guerreiro1234",
            "body": "Escreve para pessoa@example.cv.",
            "status": "pending",
            "created_at": "2026-09-26T12:00:00Z",
        }]
        with patch("sph.community.urlopen", return_value=FakeResponse(returned)):
            result = SupabaseCommunity(config()).list_pending_posts()

        self.assertEqual(result[0]["review_flags"], ["email"])

    def test_hiding_is_limited_to_pending_or_published_posts(self) -> None:
        returned = [{
            "id": POST_ID,
            "pseudonym": "Guerreiro1234",
            "body": "Partilha ocultada.",
            "status": "hidden",
            "created_at": "2026-09-26T12:00:00Z",
        }]
        with patch("sph.community.urlopen", return_value=FakeResponse(returned)) as urlopen_mock:
            SupabaseCommunity(config()).moderate_post(POST_ID, "hidden")

        self.assertIn("status=in.(pending,published)", urlopen_mock.call_args.args[0].full_url)

    def test_moderation_rejects_a_stale_transition(self) -> None:
        with patch("sph.community.urlopen", return_value=FakeResponse([])):
            with self.assertRaisesRegex(CommunityInputError, "estado atual"):
                SupabaseCommunity(config()).moderate_post(POST_ID, "published")

    def test_report_checks_visibility_before_inserting(self) -> None:
        responses = [FakeResponse([{"id": POST_ID}]), FakeResponse([{"id": "report-id"}])]
        with patch("sph.community.urlopen", side_effect=responses) as urlopen_mock:
            result = SupabaseCommunity(config()).report_post(USER_ID, POST_ID, "unsafe")

        self.assertEqual(result, {"reported": True})
        report_payload = json.loads(urlopen_mock.call_args_list[1].args[0].data)
        self.assertEqual(report_payload["reporter_id"], USER_ID)
        self.assertEqual(report_payload["reason"], "unsafe")

    def test_browser_has_no_direct_community_policy(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")

        self.assertIn('drop policy if exists "Public reads moderated posts"', schema)
        self.assertIn('drop policy if exists "Members submit pending posts"', schema)
        self.assertIn('drop policy if exists "Members report published posts"', schema)
        self.assertNotIn('create policy "Public reads moderated posts"', schema)
        self.assertNotIn('create policy "Members submit pending posts"', schema)
        self.assertNotIn('create policy "Members report published posts"', schema)



if __name__ == "__main__":
    unittest.main()
