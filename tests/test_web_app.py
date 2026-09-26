from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


class AppMarkupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.view_sections: list[str] = []
        self.nav_views: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        classes = set((values.get("class") or "").split())
        if "view-section" in classes and values.get("data-section"):
            self.view_sections.append(values["data-section"] or "")
        if tag == "button" and values.get("data-view"):
            self.nav_views.append(values["data-view"] or "")


class WebAppStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index_text = (PUBLIC / "index.html").read_text(encoding="utf-8")
        cls.parser = AppMarkupParser()
        cls.parser.feed(cls.index_text)

    def test_main_views_and_bottom_navigation_match(self) -> None:
        expected = {"meditation", "journey", "wellness", "help", "about"}

        self.assertEqual(set(self.parser.view_sections), expected)
        self.assertEqual(set(self.parser.nav_views), expected)
        self.assertEqual(len(self.parser.nav_views), len(expected))

    def test_critical_controls_exist_once(self) -> None:
        counts = Counter(self.parser.ids)
        self.assertFalse([element_id for element_id, count in counts.items() if count > 1])

        critical = {
            "more-button",
            "sos-button",
            "complete-button",
            "share-button",
            "story-button",
            "export-data",
            "delete-local-data",
            "delete-account",
            "account-email-form",
            "verified-meeting-list",
            "verified-help-list",
            "help-directory-source",
        }
        self.assertFalse(critical.difference(counts))

    def test_manifest_and_service_worker_assets_exist(self) -> None:
        manifest = json.loads((PUBLIC / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["start_url"], "/#meditacao")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(
            {shortcut["url"] for shortcut in manifest["shortcuts"]},
            {"/#meditacao", "/#jornada", "/#ajuda"},
        )

        worker = (PUBLIC / "sw.js").read_text(encoding="utf-8")
        assets_block = re.search(r"const CORE_ASSETS = \[(.*?)\];", worker, re.S)
        self.assertIsNotNone(assets_block)
        assets = re.findall(r'"([^"]+)"', assets_block.group(1))
        for asset in assets:
            relative = "index.html" if asset == "/" else asset.lstrip("/")
            self.assertTrue((PUBLIC / relative).is_file(), asset)

        self.assertIn('url.pathname.startsWith("/api/")', worker)
        self.assertIn('pathname.startsWith("/expo")', worker)
        self.assertIn('pathname.startsWith("/privacidade")', worker)

    def test_vercel_routes_dynamic_api_before_static_files(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        routes = config["routes"]

        self.assertEqual(routes[0]["src"], "/api/(.*)")
        self.assertEqual(routes[0]["dest"], "/api/index.py")
        self.assertIn({"src": "/expo/?", "dest": "/public/expo/index.html"}, routes)
        self.assertIn({"src": "/privacidade/?", "dest": "/public/privacidade/index.html"}, routes)

    def test_vercel_security_and_cache_headers_are_present(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        rules = {rule["source"]: {item["key"]: item["value"] for item in rule["headers"]} for rule in config["headers"]}

        self.assertEqual(rules["/sw.js"]["Cache-Control"], "public, max-age=0, must-revalidate")
        self.assertEqual(rules["/api/(.*)"]["Cache-Control"], "private, no-store")
        security = rules["/(.*)"]
        self.assertIn("frame-ancestors 'none'", security["Content-Security-Policy"])
        self.assertIn("https://*.supabase.co", security["Content-Security-Policy"])
        self.assertIn("https://www.youtube.com", security["Content-Security-Policy"])
        self.assertEqual(security["X-Content-Type-Options"], "nosniff")
        self.assertEqual(security["X-Frame-Options"], "DENY")

    def test_server_secrets_are_not_shipped_in_public_files(self) -> None:
        public_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in PUBLIC.rglob("*")
            if path.is_file()
        )

        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", public_text)
        self.assertNotIn("OPENAI_API_KEY", public_text)


if __name__ == "__main__":
    unittest.main()
