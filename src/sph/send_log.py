from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class SendLogEntry:
    send_date: str
    month_day: str
    channel: str
    destination_id: str | None
    status: str
    message_hash: str
    error_message: str | None
    sent_at: str


class JsonlSendLog:
    def __init__(self, path: Path):
        self.path = path

    def list(self, limit: int | None = None) -> list[SendLogEntry]:
        if not self.path.exists():
            return []
        entries: list[str] | deque[str]
        entries = deque(maxlen=limit) if limit is not None else []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    entries.append(line)
        return [SendLogEntry(**json.loads(line)) for line in entries]

    def already_sent(self, send_date: str, channel: str, destination_id: str | None) -> bool:
        return any(
            entry.send_date == send_date
            and entry.channel == channel
            and entry.destination_id == destination_id
            and entry.status == "sent"
            for entry in self.list()
        )

    def append(self, entry: SendLogEntry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def now_iso(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).isoformat(timespec="seconds")
