from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from sph.config import settings
from sph.repository import MeditationRepository
from sph.service import DailyMeditationService


repository = MeditationRepository(settings.data_path)
service = DailyMeditationService(repository, settings.timezone)
PUBLIC_DIR = settings.data_path.parents[1] / "public"


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        self.handle_request(write_body=False)

    def do_GET(self) -> None:
        self.handle_request(write_body=True)

    def handle_request(self, write_body: bool) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/v1/health":
                self.respond({"status": "ok", "timezone": settings.timezone}, write_body=write_body)
            elif path == "/api/v1/today":
                self.respond(service.today().__dict__, write_body=write_body)
            elif path == "/api/v1/today/preview":
                self.respond({"message": service.format_message(service.today())}, write_body=write_body)
            elif path == "/api/v1/meditations":
                self.respond([item.__dict__ for item in repository.all()], write_body=write_body)
            elif path.startswith("/api/v1/day/"):
                month_day = path.rsplit("/", 1)[-1]
                self.respond(service.by_month_day(month_day).__dict__, write_body=write_body)
            else:
                self.serve_static(path, write_body=write_body)
        except ValueError as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.BAD_REQUEST, write_body=write_body)
        except LookupError as exc:
            self.respond({"detail": str(exc)}, HTTPStatus.NOT_FOUND, write_body=write_body)

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
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if write_body:
            self.wfile.write(body)

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
