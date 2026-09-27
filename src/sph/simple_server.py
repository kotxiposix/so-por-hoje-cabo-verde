from __future__ import annotations

import argparse
import json
import mimetypes
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from sph.account_deletion import (
    AccountAuthenticationError,
    AccountDeletionConfig,
    AccountServiceError,
    SupabaseAccountDeletion,
    bearer_token,
)
from sph.ai_support import DailySupportRequest, build_daily_support, support_to_dict
from sph.config import settings
from sph.help_directory import HelpDirectoryConfig, HelpDirectoryServiceError, SupabaseHelpDirectory
from sph.public_config import public_runtime_config
from sph.push_delivery import PushDeliveryConfig, deliver_due_notifications, is_authorized
from sph.repository import MeditationRepository
from sph.service import DailyMeditationService


repository = MeditationRepository(settings.data_path)
service = DailyMeditationService(repository, settings.timezone)
PUBLIC_DIR = settings.data_path.parents[1] / "public"
MAX_JSON_BODY_BYTES = 64 * 1024
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
    "script-src 'self' https://challenges.cloudflare.com; style-src 'self'; img-src 'self' data: blob:; font-src 'self'; "
    "connect-src 'self' https://*.supabase.co; "
    "frame-src https://www.youtube-nocookie.com https://challenges.cloudflare.com; worker-src 'self'; manifest-src 'self'; "
    "form-action 'self' mailto:"
)
SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}
NO_STORE = "private, no-store"
REVALIDATE = "public, max-age=0, must-revalidate"


class RequestBodyTooLarge(ValueError):
    pass


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        self.handle_request(write_body=False)

    def do_GET(self) -> None:
        self.handle_request(write_body=True)

    def do_POST(self) -> None:
        self.handle_post()

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/v1/account":
            self.respond({"detail": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            token = bearer_token(self.headers.get("Authorization"))
            SupabaseAccountDeletion(AccountDeletionConfig.from_environment()).delete_for_access_token(token)
            self.respond({"deleted": True})
        except AccountAuthenticationError as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.UNAUTHORIZED)
        except AccountServiceError as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)

    def handle_request(self, write_body: bool) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/v1/health":
                self.respond({"status": "ok", "timezone": settings.timezone}, write_body=write_body)
            elif path == "/api/v1/config":
                self.respond(public_runtime_config(), write_body=write_body)
            elif path == "/api/v1/today":
                self.respond(service.today().__dict__, write_body=write_body)
            elif path == "/api/v1/today/preview":
                self.respond({"message": service.format_message(service.today())}, write_body=write_body)
            elif path == "/api/v1/meditations":
                self.respond([item.__dict__ for item in repository.all()], write_body=write_body)
            elif path == "/api/v1/help/resources":
                directory = SupabaseHelpDirectory(HelpDirectoryConfig.from_environment())
                self.respond(directory.list_verified(), write_body=write_body)
            elif path.startswith("/api/v1/day/"):
                month_day = path.rsplit("/", 1)[-1]
                self.respond(service.by_month_day(month_day).__dict__, write_body=write_body)
            else:
                self.serve_static(path, write_body=write_body)
        except ValueError as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.BAD_REQUEST, write_body=write_body)
        except LookupError as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.NOT_FOUND, write_body=write_body)
        except HelpDirectoryServiceError as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE, write_body=write_body)

    def handle_post(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/v1/ai/daily-support":
                payload = self.read_json_body()
                daily_payload = payload.get("daily") or {}
                requested_date = payload.get("meditation_date") or daily_payload.get("date")
                daily = service.for_date(date.fromisoformat(requested_date)) if requested_date else service.today()
                support = build_daily_support(
                    DailySupportRequest(
                        daily=daily,
                        user_state=str(payload.get("user_state") or ""),
                        clean_days=int(payload.get("clean_days") or 0),
                        reading_streak=int(payload.get("reading_streak") or 0),
                        language=str(payload.get("language") or "pt-CV"),
                    )
                )
                self.respond(support_to_dict(support))
            elif path == "/api/v1/internal/push/deliver":
                config = PushDeliveryConfig.from_environment()
                if not is_authorized(self.headers.get("Authorization"), config.cron_secret):
                    self.respond({"detail": "Nao autorizado"}, HTTPStatus.UNAUTHORIZED)
                    return
                self.respond(deliver_due_notifications(config))
            else:
                self.respond({"detail": "Not found"}, HTTPStatus.NOT_FOUND)
        except RequestBodyTooLarge as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        except (TypeError, ValueError) as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)

    def read_json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > MAX_JSON_BODY_BYTES:
            raise RequestBodyTooLarge("Pedido JSON excede o limite de 64 KB")
        body = self.rfile.read(length)
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Pedido JSON invalido")
        return payload

    def log_message(self, format: str, *args: object) -> None:
        return

    def respond(
        self,
        payload: object,
        status: HTTPStatus = HTTPStatus.OK,
        write_body: bool = True,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status.value)
        self.send_standard_headers(NO_STORE)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if write_body:
            self.wfile.write(body)

    def serve_static(self, path: str, write_body: bool = True) -> None:
        relative_path = "index.html" if path in {"", "/"} else path.lstrip("/")
        file_path = (PUBLIC_DIR / relative_path).resolve()
        if file_path.is_dir():
            file_path = (file_path / "index.html").resolve()

        if not self._is_public_file(file_path):
            self.respond({"detail": "Not found"}, HTTPStatus.NOT_FOUND, write_body=write_body)
            return

        body = file_path.read_bytes()
        content_type, _ = mimetypes.guess_type(file_path)
        self.send_response(HTTPStatus.OK.value)
        self.send_standard_headers(self.static_cache_control(path))
        self.send_header("Content-Type", self.content_type(file_path, content_type))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if write_body:
            self.wfile.write(body)

    def send_standard_headers(self, cache_control: str) -> None:
        for key, value in SECURITY_HEADERS.items():
            self.send_header(key, value)
        self.send_header("Cache-Control", cache_control)

    @staticmethod
    def static_cache_control(path: str) -> str:
        normalized = "/" + path.lstrip("/")
        if normalized == "/sw.js":
            return REVALIDATE
        if normalized == "/admin" or normalized.startswith("/admin/"):
            return NO_STORE
        return REVALIDATE

    @staticmethod
    def content_type(file_path: Path, guessed_type: str | None = None) -> str:
        content_type = guessed_type or mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "application/json",
            "application/manifest+json",
        }:
            return f"{content_type}; charset=utf-8"
        return content_type

    def _is_public_file(self, file_path: Path) -> bool:
        try:
            return file_path.is_file() and file_path.is_relative_to(PUBLIC_DIR.resolve())
        except ValueError:
            return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor REST simples SPH.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"SPH app running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
