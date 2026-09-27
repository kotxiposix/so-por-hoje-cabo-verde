from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


class AppMarkupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.attributes_by_id: dict[str, dict[str, str | None]] = {}
        self.checkin_buttons: list[dict[str, str | None]] = []
        self.tool_buttons: list[dict[str, str | None]] = []
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
        if tag == "button" and values.get("data-tool"):
            self.tool_buttons.append(values)


class DocumentReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.references: list[str] = []
        self.unsafe_blank_references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        for name in ("href", "src"):
            if values.get(name):
                self.references.append(values[name] or "")
        if values.get("target") == "_blank" and "noreferrer" not in (values.get("rel") or "").split():
            self.unsafe_blank_references.append(values.get("href") or "")


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
            "gratitude-form",
            "sobriety-date",
            "support-plan-form",
            "history-list",
            "reminder-time",
            "show-clean-days",
            "pwa-update",
            "install-app-secondary",
            "notifications-secondary",
            "export-data",
            "delete-local-data",
            "delete-account",
            "account-email-form",
            "verified-meeting-list",
            "verified-help-list",
            "help-directory-source",
            "anonymous-form",
            "copy-support-message",
            "browse-meditations",
            "archive-modal",
            "archive-date",
            "privacy-principle-copy",
            "privacy-storage-summary",
            "privacy-storage-detail",
            "gratitude-privacy-note",
            "journey-privacy-intro",
            "privacy-faq-answer",
        }
        self.assertFalse(critical.difference(counts))

    def test_daily_support_and_checkin_options_match_the_product_map(self) -> None:
        self.assertEqual(
            {button["data-tool"] for button in self.parser.tool_buttons},
            {"activity", "phrase", "challenge"},
        )
        self.assertEqual(
            {button["data-checkin"] for button in self.parser.checkin_buttons},
            {"firme", "ansioso", "risco", "consumo"},
        )
        self.assertTrue(all(button.get("aria-pressed") == "false" for button in self.parser.checkin_buttons))

    def test_local_page_references_and_anchors_resolve(self) -> None:
        documents: dict[str, tuple[Path, DocumentReferenceParser]] = {}
        for html_path in PUBLIC.rglob("*.html"):
            relative = html_path.relative_to(PUBLIC)
            route = "/" if relative == Path("index.html") else f"/{relative.parent.as_posix()}/"
            parser = DocumentReferenceParser()
            parser.feed(html_path.read_text(encoding="utf-8"))
            documents[route] = (html_path, parser)

        route_files = {
            "/": PUBLIC / "index.html",
            "/expo": PUBLIC / "expo" / "index.html",
            "/expo/": PUBLIC / "expo" / "index.html",
            "/privacidade": PUBLIC / "privacidade" / "index.html",
            "/privacidade/": PUBLIC / "privacidade" / "index.html",
            "/admin": PUBLIC / "admin" / "index.html",
            "/admin/": PUBLIC / "admin" / "index.html",
        }
        virtual_app_hashes = {"meditacao", "jornada", "viver-saudavel", "ajuda", "sobre"}

        for route, (html_path, parser) in documents.items():
            self.assertFalse(parser.unsafe_blank_references, str(html_path))
            base_url = f"https://local.test{route}"
            for reference in parser.references:
                parsed_reference = urlparse(reference)
                if parsed_reference.scheme in {"http", "https", "mailto", "tel", "data"}:
                    continue

                resolved = urlparse(urljoin(base_url, reference))
                target_path = resolved.path or "/"
                target_file = route_files.get(target_path, PUBLIC / target_path.lstrip("/"))
                self.assertTrue(target_file.is_file(), f"{html_path}: {reference}")

                if not resolved.fragment:
                    continue
                if target_path == "/" and resolved.fragment in virtual_app_hashes:
                    continue

                target_route = target_path
                if target_route not in documents and not target_route.endswith("/"):
                    target_route = f"{target_route}/"
                target_document = documents.get(target_route)
                self.assertIsNotNone(target_document, f"{html_path}: {reference}")
                self.assertIn(resolved.fragment, target_document[1].ids, f"{html_path}: {reference}")

        for css_path in PUBLIC.rglob("*.css"):
            css = css_path.read_text(encoding="utf-8")
            for reference in re.findall(r"url\([\"']?([^\"')]+)", css):
                if urlparse(reference).scheme or reference.startswith("data:"):
                    continue
                target = (css_path.parent / reference.split("?", 1)[0]).resolve()
                self.assertTrue(target.is_file(), f"{css_path}: {reference}")

    def test_manifest_and_service_worker_assets_exist(self) -> None:
        manifest = json.loads((PUBLIC / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["start_url"], "/#meditacao")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(
            {shortcut["url"] for shortcut in manifest["shortcuts"]},
            {"/#meditacao", "/#jornada", "/#ajuda"},
        )

        worker = (PUBLIC / "sw.js").read_text(encoding="utf-8")
        self.assertIn('const CACHE_NAME = "sph-shell-v49"', worker)
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
        self.assertIn("await self.clients.claim()", worker)
        self.assertNotIn("\n  self.clients.claim();", worker)

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
        self.assertIn('from "./privacy-copy.mjs"', script)
        self.assertIn('<script type="module" src="app.js"></script>', self.index_text)

        backup_parser = (PUBLIC / "journey-backup.mjs").read_text(encoding="utf-8")
        self.assertIn("JOURNEY_BACKUP_VERSION = 1", backup_parser)
        self.assertIn("MAX_JOURNEY_BACKUP_BYTES = 1_000_000", backup_parser)

    def test_push_notification_ignores_remote_lock_screen_text(self) -> None:
        service_worker = (PUBLIC / "sw.js").read_text(encoding="utf-8")

        self.assertIn('const PUSH_TITLE = "Só Por Hoje"', service_worker)
        self.assertIn('const PUSH_BODY = "A meditação de hoje está pronta. Um dia de cada vez."', service_worker)
        self.assertIn("showNotification(PUSH_TITLE", service_worker)
        self.assertIn("body: PUSH_BODY", service_worker)
        self.assertNotIn("payload.title ||", service_worker)
        self.assertNotIn("payload.body ||", service_worker)

    def test_vercel_routes_dynamic_api_before_static_files(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        routes = config["routes"]

        self.assertEqual(routes[0]["src"], "/api/(.*)")
        self.assertEqual(routes[0]["dest"], "/api/index.py")
        self.assertIn({"src": "/admin/?", "dest": "/public/admin/index.html"}, routes)
        self.assertIn({"src": "/expo/?", "dest": "/public/expo/index.html"}, routes)
        self.assertIn({"src": "/privacidade/?", "dest": "/public/privacidade/index.html"}, routes)

    def test_vercel_security_and_cache_headers_are_present(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        rules = {rule["source"]: {item["key"]: item["value"] for item in rule["headers"]} for rule in config["headers"]}

        self.assertEqual(rules["/sw.js"]["Cache-Control"], "public, max-age=0, must-revalidate")
        self.assertEqual(rules["/api/(.*)"]["Cache-Control"], "private, no-store")
        self.assertEqual(rules["/admin"]["Cache-Control"], "private, no-store")
        self.assertEqual(rules["/admin/(.*)"]["Cache-Control"], "private, no-store")
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

    def test_public_scripts_do_not_build_dynamic_html(self) -> None:
        scripts = [*PUBLIC.rglob("*.js"), *PUBLIC.rglob("*.mjs")]

        self.assertTrue(scripts)
        for path in scripts:
            source = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(PUBLIC)):
                self.assertNotIn(".innerHTML", source)
                self.assertNotIn("insertAdjacentHTML", source)
                self.assertNotIn("document.write", source)
                self.assertNotIn("new Function", source)
                self.assertNotIn("eval(", source)

    def test_keyboard_and_assistive_technology_contracts(self) -> None:
        app = self.parser.attributes_by_id["app-content"]
        self.assertEqual(app["class"], "app-shell")
        self.assertEqual(app["tabindex"], "-1")
        self.assertEqual(self.parser.attributes_by_id["view-announcement"].get("aria-live"), "polite")
        self.assertIn('class="skip-link" href="#app-content"', self.index_text)

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
        self.assertIn("function handleBottomNavigationKeydown", script)
        self.assertIn('["ArrowLeft", "ArrowRight", "Home", "End"]', script)
        self.assertIn('button.addEventListener("keydown", handleBottomNavigationKeydown)', script)
        self.assertIn('els.viewAnnouncement.textContent = `Área ${viewLabels[view]} aberta.`', script)
        self.assertIn('event.key === "Escape" && activeModalClose', script)
        self.assertIn("function renderArchiveMeditation", script)
        self.assertIn("function loadMeditationForDate", script)
        self.assertIn("function openArchiveForDate", script)
        self.assertIn("item.dataset.historyDate = day", script)
        self.assertIn("gratitude.textContent = state.progress.gratitudes[day]", script)
        self.assertNotIn(".innerHTML", script)
        self.assertNotIn("escapeHtml", script)
        self.assertIn("function refreshForNewDay", script)
        self.assertIn("function scheduleDayRefreshCheck", script)
        self.assertIn("refreshForNewDay();\n    scheduleSessionReminder();", script)
        self.assertIn("function getInstallGuidance", script)
        self.assertIn("function updateInstallAction", script)
        self.assertIn("function removeAnonymousShare", script)
        self.assertIn('const SUPPORT_CACHE_VERSION = "v2"', script)
        self.assertIn("function clearLegacySupportCache", script)
        self.assertIn("clearLegacySupportCache();", script)
        self.assertIn('`${currentPrefix}local:`', script)
        self.assertNotIn('const supportMode = authorization ? "ai" : "local"', script)
        self.assertIn("remove.dataset.anonymousDelete = String(index)", script)
        self.assertIn('saveProgress({ touch: false, sync: false })', script)
        self.assertEqual(self.parser.attributes_by_id["pwa-install-status"].get("role"), "status")
        self.assertIn("openPrayer(sourceButton)", script)
        self.assertIn('showView("help", { updateHistory: true })', script)
        self.assertIn("window.requestAnimationFrame(() => els.sosButton.focus())", script)
        self.assertIn("prefers-reduced-motion: reduce", script)
        self.assertIn(":focus-visible", styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)

    def test_exhibition_keyboard_and_selection_contracts(self) -> None:
        expo = (PUBLIC / "expo" / "index.html").read_text(encoding="utf-8")
        script = (PUBLIC / "expo" / "page.js").read_text(encoding="utf-8")
        styles = (PUBLIC / "expo" / "styles.css").read_text(encoding="utf-8")

        self.assertIn('role="tab" aria-selected="true" aria-controls="collection-sobriu" tabindex="0"', expo)
        self.assertIn('role="tabpanel" aria-labelledby="collection-tab-sobriu"', expo)
        self.assertIn('aria-pressed="true" data-video=', expo)
        self.assertIn('aria-pressed="false" data-video=', expo)
        self.assertIn("siteMenu.inert = mobileMenuMedia.matches && !isOpen", script)
        self.assertIn('event.key === "Escape"', script)
        self.assertIn('["ArrowLeft", "ArrowRight", "Home", "End"]', script)
        self.assertIn('item.setAttribute("aria-pressed", String(isActive))', script)
        self.assertIn("iframe.title = button.textContent", script)
        self.assertIn(":focus-visible", styles)
        self.assertIn("[hidden]", styles)
        self.assertIn("display: none !important", styles)

    def test_community_client_is_gated_authenticated_and_text_safe(self) -> None:
        script = (PUBLIC / "app.js").read_text(encoding="utf-8")

        self.assertIn("accountState.communityEnabled = Boolean(config.features?.community)", script)
        self.assertIn('fetch("/api/v1/community/posts?limit=20"', script)
        self.assertIn('Authorization: `Bearer ${session.access_token}`', script)
        self.assertIn("Partilha recebida. Só ficará pública depois de revisão humana.", script)
        self.assertIn("body.textContent = post.body", script)
        self.assertNotIn("anonymousFeed.innerHTML", script)
        self.assertEqual(self.parser.attributes_by_id["anonymous-status"].get("aria-live"), "polite")

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

    def test_staff_admin_is_separate_and_never_cached_offline(self) -> None:
        admin_html = (PUBLIC / "admin" / "index.html").read_text(encoding="utf-8")
        admin_styles = (PUBLIC / "admin" / "admin.css").read_text(encoding="utf-8")
        admin_script = (PUBLIC / "admin" / "admin.js").read_text(encoding="utf-8")
        service_worker = (PUBLIC / "sw.js").read_text(encoding="utf-8")

        self.assertIn('name="robots" content="noindex, nofollow, noarchive"', admin_html)
        self.assertIn('id="email-form" hidden', admin_html)
        self.assertIn('id="community-view"', admin_html)
        self.assertIn('id="directory-view"', admin_html)
        self.assertIn('id="operations-view"', admin_html)
        self.assertIn('id="content-view"', admin_html)
        self.assertIn('class="admin-tabs" role="tablist"', admin_html)
        self.assertIn('role="tab" aria-selected="false" aria-controls="community-view" tabindex="-1"', admin_html)
        self.assertIn('role="tabpanel" aria-labelledby="community-tab community-title"', admin_html)
        self.assertIn('href="/admin/admin.css?v=6"', admin_html)
        self.assertIn('src="/admin/admin.js?v=6"', admin_html)
        self.assertNotIn('href="admin.css', admin_html)
        self.assertNotIn('src="admin.js', admin_html)
        self.assertIn('sendOtp(pendingEmail, { createUser: false })', admin_script)
        self.assertIn('platformRequest("/api/v1/admin/me")', admin_script)
        self.assertIn('from "../account-client.mjs?staff=3"', admin_script)
        self.assertIn('platformRequest("/api/v1/admin/operations/send-logs?limit=100")', admin_script)
        self.assertIn('platformRequest("/api/v1/admin/operations/audit-events?limit=100")', admin_script)
        self.assertIn('id="audit-list"', admin_html)
        self.assertIn('const initialView = canOperate ? "operations"', admin_script)
        self.assertIn('platformRequest("/api/v1/admin/content?limit=500")', admin_script)
        self.assertIn('setStatus(error.message || "Não foi possível carregar esta área."', admin_script)
        self.assertIn("els.email_form.hidden = false", admin_script)
        self.assertIn('config.features?.staffAdmin', admin_script)
        self.assertIn("sessionStorage.getItem(SESSION_KEY)", admin_script)
        self.assertIn('if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key))', admin_script)
        self.assertIn("tab.tabIndex = active ? 0 : -1", admin_script)
        self.assertNotIn("localStorage", admin_script)
        self.assertIn("[hidden] { display: none !important; }", admin_styles)
        self.assertIn('url.pathname.startsWith("/admin")', service_worker)
        self.assertIn('fetch(request, { cache: "no-store" })', service_worker)

        core_assets = service_worker.split("const CORE_ASSETS = [", 1)[1].split("];", 1)[0]
        self.assertNotIn("/admin", core_assets)
        self.assertNotIn('href="/admin', self.index_text)

    def test_editorial_feed_is_optional_and_uses_safe_dom_rendering(self) -> None:
        script = (PUBLIC / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="editorial-feed"', self.index_text)
        self.assertIn('id="editorial-list"', self.index_text)
        self.assertIn('fetch("/api/v1/content?limit=50"', script)
        self.assertIn("item.title || \"Conteúdo\"", script)
        self.assertIn("summary.textContent", script)
        self.assertNotIn("editorialList.innerHTML", script)

    def test_privacy_page_matches_local_backup_behavior(self) -> None:
        privacy = (PUBLIC / "privacidade" / "index.html").read_text(encoding="utf-8")

        self.assertIn("cópia JSON versionada", privacy)
        self.assertIn("aceita até 1 MB", privacy)
        self.assertIn("pede confirmação antes de substituir os dados locais", privacy)
        self.assertIn("Por defeito", privacy)
        self.assertIn("escolheres sincronizar a Jornada", privacy)
        self.assertIn("modo de privacidade reforçada do YouTube", privacy)


if __name__ == "__main__":
    unittest.main()
