from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Meditation:
    month_day: str
    title: str
    body: str
    reflection: str
    language: str = "pt-CV"
    status: str = "published"
    source: str | None = None


@dataclass(frozen=True)
class DailyMeditation:
    date: str
    weekday: str
    month_day: str
    title: str
    body: str
    reflection: str


@dataclass(frozen=True)
class SendResult:
    channel: str
    ok: bool
    destination_id: str | None = None
    message_id: str | None = None
    error: str | None = None

