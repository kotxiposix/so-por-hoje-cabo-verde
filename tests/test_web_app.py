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
        self.attributes_by_id: dict[str, dict[str, str | None]] = {}
        self.checkin_buttons: list[dict[str, str | None]] = []
        self.view_sections: list[str] = []
        self.nav_views: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
            self.attributes_by_id[values["id"] or ""] = values
        classes = set((values.get("class") or "").split())
        if "view-section" in classes and values.get("data-section"):
            self.view_sections.append(values["data-section"] or "")
        if tag == "button" and values.get("data-view"):
            self.nav_views.append(values["data-view"] or "")
        if tag == "button" and values.get("data-checkin"):
            self.checkin_buttons.append(values)


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
            "pwa-update",
            "export-data",
            "delete-local-data",
            "delete-account",
            "account-email-form",
            "verified-meeting-list",
            "verified-help-list",
            "help-directory-source",
            "browse-meditations",
            "archive-modal",
            "archive-date",
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
        self.assertIn('event.data?.type === "SKIP_WAITING"', worker)

        script = (PUBLIC / "app.js").read_text(encoding="utf-8")
        self.assertIn("function loadLocalDailySupport", script)
        self.assertRegex(
            script,
            r"if \(!authorization\) \{[\s\S]*?loadLocalDailySupport\(payload\)[\s\S]*?return support;\s*\}",
        )
        self.assertIn("function watchServiceWorkerRegistration", script)
        self.assertIn("function trackInstallingServiceWorker", script)
        self.assertIn("trackInstallingServiceWorker(registration.installing)", script)
        self.assertIn("function activateAppUpdate", script)
        self.assertIn("parseJourneyBackup", script)
        self.assertIn("MAX_JOURNEY_BACKUP_BYTES", script)
        self.assertIn("validateRemoteJourneyRecord", script)
        self.assertIn("hasRemoteJourneyConflict", script)
        self.assertIn("selectSyncableProgress", script)
        self.assertIn('from "./date-utils.mjs"', script)
        self.assertIn('<script type="module" src="app.js"></script>', self.index_text)

        backup_parser = (PUBLIC / "journey-backup.mjs").read_text(encoding="utf-8")
        self.assertIn("JOURNEY_BACKUP_VERSION = 1", backup_parser)
        self.assertIn("MAX_JOURNEY_BACKUP_BYTES = 1_000_000", backup_parser)

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
        self.assertIn("frame-src https://www.youtube-nocookie.com", security["Content-Security-Policy"])
        self.assertNotIn("frame-src https://www.youtube.com", security["Content-Security-Policy"])
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

    def test_keyboard_and_assistive_technology_contracts(self) -> None:
        app = self.parser.attributes_by_id["app-content"]
        self.assertEqual(app["class"], "app-shell")

        for modal_id in ("prayer-modal", "tool-modal", "archive-modal", "sos-modal", "more-modal"):
            self.assertIn(f'id="{modal_id}" hidden', self.index_text)
        self.assertEqual(len(self.parser.checkin_buttons), 4)
        self.assertTrue(all(button.get("aria-pressed") == "false" for button in self.parser.checkin_buttons))
        self.assertEqual(self.parser.attributes_by_id["checkin-guidance"].get("aria-live"), "polite")
        self.assertEqual(self.parser.attributes_by_id["status-card"].get("role"), "status")

        script = (PUBLIC / "app.js").read_text(encoding="utf-8")
        styles = (PUBLIC / "styles.css").read_text(encoding="utf-8")
        self.assertIn("els.appContent.inert = true", script)
        self.assertIn('els.appContent.setAttribute("aria-hidden", "true")', script)
        self.assertIn("disabledBackgroundFocus", script)
        self.assertIn("function trapModalFocus", script)
        self.assertIn('event.key === "Escape" && activeModalClose', script)
        self.assertIn("function renderArchiveMeditation", script)
        self.assertIn("function loadMeditationForDate", script)
        self.assertIn("function openArchiveForDate", script)
        self.assertIn('data-history-date="${day}"', script)
        self.assertIn("function refreshForNewDay", script)
        self.assertIn("function scheduleDayRefreshCheck", script)
        self.assertIn("refreshForNewDay();\n    scheduleSessionReminder();", script)
        self.assertIn("openPrayer(sourceButton)", script)
        self.assertIn('showView("help", { updateHistory: true })', script)
        self.assertIn("window.requestAnimationFrame(() => els.sosButton.focus())", script)
        self.assertIn("prefers-reduced-motion: reduce", script)
        self.assertIn(":focus-visible", styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)

    def test_bottom_navigation_and_long_help_labels_are_responsive(self) -> None:
        styles = (PUBLIC / "styles.css").read_text(encoding="utf-8")

        self.assertRegex(styles, r"\.bottom-nav\s*\{[^}]*position:\s*fixed")
        self.assertRegex(styles, r"\.bottom-nav\s*\{[^}]*grid-template-columns:\s*repeat\(5,\s*1fr\)")
        self.assertRegex(styles, r"\.resource-heading\s*\{[^}]*flex-wrap:\s*wrap")
        self.assertRegex(styles, r"\.resource-heading strong\s*\{[^}]*overflow-wrap:\s*anywhere")

    def test_static_help_contacts_distinguish_official_and_unconfirmed_details(self) -> None:
        self.assertIn('href="tel:+2382620699">Ligar 262 06 99</a>', self.index_text)
        self.assertIn('href="tel:+2382620122">Ligar 262 01 22</a>', self.index_text)
        self.assertIn("Contacto oficial", self.index_text)
        self.assertIn("9h30 indicado pela comunidade", self.index_text)
        self.assertIn("contactos do Ministério da Saúde", self.index_text)

    def test_media_outside_the_initial_view_is_deferred(self) -> None:
        self.assertIn(
            'src="expo/hero.jpg" alt="Capa da exposição Só Por Hoje" loading="lazy" decoding="async"',
            self.index_text,
        )
        self.assertRegex(
            self.index_text,
            r'title="Playlist do podcast Só Por Hoje Cabo Verde"\s+loading="lazy"',
        )
        self.assertNotIn("youtube.com/embed", self.index_text)
        self.assertIn("youtube-nocookie.com/embed", self.index_text)

        expo = (PUBLIC / "expo" / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="hero-image" src="/expo/hero-banner.jpg"', expo)
        self.assertIn('fetchpriority="high" decoding="async"', expo)
        self.assertIn(
            'src="/expo/sandro-profile.png" alt="Retrato de Sandro Fonseca" loading="lazy" decoding="async"',
            expo,
        )
        self.assertNotIn("youtube.com/embed", expo)
        self.assertIn("youtube-nocookie.com/embed", expo)

        expo_script = (PUBLIC / "expo" / "page.js").read_text(encoding="utf-8")
        self.assertIn("youtube-nocookie.com/embed", expo_script)
        self.assertNotIn("youtube.com/embed", expo_script)

    def test_privacy_page_matches_local_backup_behavior(self) -> None:
        privacy = (PUBLIC / "privacidade" / "index.html").read_text(encoding="utf-8")

        self.assertIn("cópia JSON versionada", privacy)
        self.assertIn("aceita até 1 MB", privacy)
        self.assertIn("pede confirmação antes de substituir os dados locais", privacy)
        self.assertIn("modo de privacidade reforçada do YouTube", privacy)


if __name__ == "__main__":
    unittest.main()
