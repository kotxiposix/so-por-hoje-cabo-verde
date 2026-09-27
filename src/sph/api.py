from __future__ import annotations

from datetime import date

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

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
from sph.community import (
    CommunityConfig,
    CommunityConflictError,
    CommunityInputError,
    CommunityLimitError,
    CommunityServiceError,
    SupabaseCommunity,
)
from sph.config import settings
from sph.help_directory import (
    HelpDirectoryConfig,
    HelpDirectoryInputError,
    HelpDirectoryServiceError,
    SupabaseHelpDirectory,
)
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


class DailyMeditationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str = Field(min_length=10, max_length=10)
    weekday: str = Field(min_length=1, max_length=30)
    month_day: str = Field(pattern=r"^\d{2}-\d{2}$")
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10_000)
    reflection: str = Field(min_length=1, max_length=2_000)


class AiDailySupportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daily: DailyMeditationPayload | None = None
    user_state: str = Field(default="", max_length=20)
    clean_days: int = Field(default=0, ge=0, le=100_000)
    reading_streak: int = Field(default=0, ge=0, le=3_660)
    language: str = Field(default="pt-CV", min_length=2, max_length=12)


class CommunityPostPayload(BaseModel):
    body: str = Field(min_length=1, max_length=280)


class CommunityReportPayload(BaseModel):
    reason: str = Field(min_length=1, max_length=32)
    details: str | None = Field(default=None, max_length=500)


class CommunityModerationPayload(BaseModel):
    status: str = Field(min_length=1, max_length=20)
    note: str | None = Field(default=None, max_length=500)


class HelpResourcePayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    island: str | None = Field(default=None, max_length=60)
    municipality: str | None = Field(default=None, max_length=80)
    category: str = Field(min_length=1, max_length=40)
    description: str | None = Field(default=None, max_length=1000)
    phone: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=254)
    website: str | None = Field(default=None, max_length=500)
    schedule: list[str] = Field(default_factory=list, max_length=20)
    is_emergency: bool = False
    source_url: str | None = Field(default=None, max_length=500)


class HelpVerificationPayload(BaseModel):
    review_days: int = Field(default=90, ge=1, le=365)


def require_admin_access(authorization: str | None) -> None:
    if not admin_access_allowed(authorization):
        raise HTTPException(status_code=401, detail="Não autorizado")


def community_service() -> SupabaseCommunity:
    try:
        return SupabaseCommunity(CommunityConfig.from_environment())
    except CommunityServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def authenticated_user_id(authorization: str | None) -> str:
    try:
        token = bearer_token(authorization)
        config = AccountDeletionConfig.from_environment()
        return SupabaseAccountDeletion(config).resolve_user_id(token)
    except AccountAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AccountServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def help_directory_service() -> SupabaseHelpDirectory:
    try:
        return SupabaseHelpDirectory(HelpDirectoryConfig.from_environment())
    except HelpDirectoryServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


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
        daily = service.for_date(date.fromisoformat(payload.daily.date)) if payload.daily else service.today()
    except (TypeError, ValueError, LookupError) as exc:
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


@app.get("/api/v1/community/posts")
def community_posts(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, object]]:
    try:
        return community_service().list_published_posts(limit)
    except CommunityServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/v1/community/posts")
def create_community_post(
    payload: CommunityPostPayload,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    community = community_service()
    user_id = authenticated_user_id(authorization)
    try:
        return community.create_pending_post(user_id, payload.body)
    except CommunityInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CommunityLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except CommunityServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/v1/community/posts/{post_id}/reports")
def report_community_post(
    post_id: str,
    payload: CommunityReportPayload,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    community = community_service()
    user_id = authenticated_user_id(authorization)
    try:
        return community.report_post(user_id, post_id, payload.reason, payload.details)
    except CommunityInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CommunityConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CommunityServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/v1/admin/community/pending")
def pending_community_posts(
    limit: int = Query(default=50, ge=1, le=200),
    authorization: str | None = Header(default=None),
) -> list[dict[str, object]]:
    require_admin_access(authorization)
    try:
        return community_service().list_pending_posts(limit)
    except CommunityServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.patch("/api/v1/admin/community/posts/{post_id}")
def moderate_community_post(
    post_id: str,
    payload: CommunityModerationPayload,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    require_admin_access(authorization)
    try:
        return community_service().moderate_post(post_id, payload.status, payload.note)
    except CommunityInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CommunityServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/v1/help/resources")
def verified_help_resources(limit: int = Query(default=100, ge=1, le=200)) -> list[dict[str, object]]:
    try:
        return help_directory_service().list_verified(limit)
    except HelpDirectoryServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/v1/admin/help/resources")
def help_resources_for_review(
    limit: int = Query(default=200, ge=1, le=500),
    authorization: str | None = Header(default=None),
) -> list[dict[str, object]]:
    require_admin_access(authorization)
    try:
        return help_directory_service().list_for_review(limit)
    except HelpDirectoryServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/v1/admin/help/resources")
def create_help_resource(
    payload: HelpResourcePayload,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    require_admin_access(authorization)
    try:
        return help_directory_service().create_draft(payload.model_dump())
    except HelpDirectoryInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HelpDirectoryServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.put("/api/v1/admin/help/resources/{resource_id}")
def update_help_resource(
    resource_id: str,
    payload: HelpResourcePayload,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    require_admin_access(authorization)
    try:
        return help_directory_service().update_draft(resource_id, payload.model_dump())
    except HelpDirectoryInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HelpDirectoryServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/v1/admin/help/resources/{resource_id}/verify")
def verify_help_resource(
    resource_id: str,
    payload: HelpVerificationPayload,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    require_admin_access(authorization)
    try:
        return help_directory_service().verify(resource_id, payload.review_days)
    except HelpDirectoryInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HelpDirectoryServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/v1/admin/help/resources/{resource_id}/retire")
def retire_help_resource(
    resource_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    require_admin_access(authorization)
    try:
        return help_directory_service().retire(resource_id)
    except HelpDirectoryInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HelpDirectoryServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


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
def send_logs(
    limit: int = Query(default=100, ge=1, le=500),
    authorization: str | None = Header(default=None),
) -> list[dict[str, str | None]]:
    require_admin_access(authorization)
    return [entry.__dict__ for entry in send_log.list(limit=limit)]


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
