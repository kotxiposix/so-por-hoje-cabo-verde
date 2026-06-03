from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException

from sph.channels.console import ConsoleChannel
from sph.config import settings
from sph.repository import MeditationRepository
from sph.send_log import JsonlSendLog
from sph.sender import DailySender
from sph.service import DailyMeditationService


repository = MeditationRepository(settings.data_path)
service = DailyMeditationService(repository, settings.timezone)
send_log = JsonlSendLog(settings.send_log_path)
sender = DailySender(service, send_log, settings.timezone)
app = FastAPI(title="So Por Hoje Cabo Verde", version="0.1.0")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "timezone": settings.timezone}


@app.get("/api/v1/today")
def today() -> dict[str, str]:
    try:
        return service.today().__dict__
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/today/preview")
def today_preview() -> dict[str, str]:
    daily = service.today()
    return {"message": service.format_message(daily)}


@app.get("/api/v1/day/{month_day}")
def by_day(month_day: str) -> dict[str, str | None]:
    try:
        return service.by_month_day(month_day).__dict__
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/meditations")
def meditations() -> list[dict[str, str | None]]:
    return [item.__dict__ for item in repository.all()]


@app.get("/api/v1/admin/send-logs")
def send_logs() -> list[dict[str, str | None]]:
    return [entry.__dict__ for entry in send_log.list()]


@app.post("/api/v1/admin/send-test")
async def send_test(force: bool = True) -> dict[str, str | bool | None]:
    daily = service.today()
    result = await sender.send_for_date(
        target=date.fromisoformat(daily.date),
        channel=ConsoleChannel(),
        destination_id="console",
        force=force,
    )
    return result.__dict__
