from __future__ import annotations

from datetime import date

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from sph.account_deletion import (
    AccountAuthenticationError,
    AccountDeletionConfig,
    AccountServiceError,
    SupabaseAccountDeletion,
    bearer_token,
)
from sph.ai_support import DailySupportRequest, build_daily_support, support_to_dict
from sph.ai_access import AiRuntimeConfig, AiUsageError, SupabaseAiUsage
from sph.channels.console import ConsoleChannel
from sph.config import settings
from sph.models import DailyMeditation
from sph.public_config import public_runtime_config
from sph.push_delivery import PushDeliveryConfig, deliver_due_notifications, is_authorized
from sph.repository import MeditationRepository
from sph.security import admin_access_allowed
from sph.send_log import JsonlSendLog
from sph.sender import DailySender
from sph.service import DailyMeditationService


repository = MeditationRepository(settings.data_path)
service = DailyMeditationService(repository, settings.timezone)
send_log = JsonlSendLog(settings.send_log_path)
sender = DailySender(service, send_log, settings.timezone)
app = FastAPI(title="So Por Hoje Cabo Verde", version="0.1.0")


class AiDailySupportPayload(BaseModel):
    daily: dict[str, str] | None = None
    user_state: str = ""
    clean_days: int = 0
    reading_streak: int = 0
    language: str = "pt-CV"


def require_admin_access(authorization: str | None) -> None:
    if not admin_access_allowed(authorization):
        raise HTTPException(status_code=401, detail="Não autorizado")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "timezone": settings.timezone}


@app.get("/api/v1/config")
def runtime_config() -> dict[str, object]:
    return public_runtime_config()


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


@app.post("/api/v1/ai/daily-support")
def ai_daily_support(
    payload: AiDailySupportPayload,
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    try:
        daily = DailyMeditation(**payload.daily) if payload.daily else service.today()
    except TypeError as exc:
        raise HTTPException(status_code=400, detail="Dados da meditação inválidos") from exc
    allow_openai = False
    runtime = AiRuntimeConfig.from_environment()
    if runtime.ready and authorization:
        try:
            token = bearer_token(authorization)
            user_id = SupabaseAccountDeletion(
                AccountDeletionConfig(runtime.supabase_url, runtime.service_role_key)
            ).resolve_user_id(token)
            allow_openai = SupabaseAiUsage(runtime).claim(user_id)
        except (AccountAuthenticationError, AccountServiceError, AiUsageError):
            allow_openai = False

    support = build_daily_support(
        DailySupportRequest(
            daily=daily,
            user_state=payload.user_state,
            clean_days=payload.clean_days,
            reading_streak=payload.reading_streak,
            language=payload.language,
        ),
        allow_openai=allow_openai,
    )
    return support_to_dict(support)


@app.post("/api/v1/internal/push/deliver")
def deliver_push_notifications(authorization: str | None = Header(default=None)) -> dict[str, int]:
    config = PushDeliveryConfig.from_environment()
    if not is_authorized(authorization, config.cron_secret):
        raise HTTPException(status_code=401, detail="Não autorizado")
    try:
        return deliver_due_notifications(config)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.delete("/api/v1/account")
def delete_account(authorization: str | None = Header(default=None)) -> dict[str, bool]:
    try:
        token = bearer_token(authorization)
        SupabaseAccountDeletion(AccountDeletionConfig.from_environment()).delete_for_access_token(token)
    except AccountAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AccountServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"deleted": True}


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
def send_logs(authorization: str | None = Header(default=None)) -> list[dict[str, str | None]]:
    require_admin_access(authorization)
    return [entry.__dict__ for entry in send_log.list()]


@app.post("/api/v1/admin/send-test")
async def send_test(
    force: bool = True,
    authorization: str | None = Header(default=None),
) -> dict[str, str | bool | None]:
    require_admin_access(authorization)
    daily = service.today()
    result = await sender.send_for_date(
        target=date.fromisoformat(daily.date),
        channel=ConsoleChannel(),
        destination_id="console",
        force=force,
    )
    return result.__dict__
