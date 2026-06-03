from __future__ import annotations

import hashlib
from datetime import date

from sph.channels.base import Channel
from sph.models import SendResult
from sph.send_log import JsonlSendLog, SendLogEntry, now_iso
from sph.service import DailyMeditationService


class DailySender:
    def __init__(self, service: DailyMeditationService, send_log: JsonlSendLog, timezone: str):
        self.service = service
        self.send_log = send_log
        self.timezone = timezone

    async def send_for_date(
        self,
        target: date,
        channel: Channel,
        destination_id: str | None = None,
        force: bool = False,
    ) -> SendResult:
        daily = self.service.for_date(target)
        message = self.service.format_message(daily)
        message_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()

        if not force and self.send_log.already_sent(daily.date, channel.name, destination_id):
            return SendResult(
                channel=channel.name,
                ok=False,
                destination_id=destination_id,
                error="Envio duplicado bloqueado por idempotencia.",
            )

        result = await channel.send(message, destination_id=destination_id)
        self.send_log.append(
            SendLogEntry(
                send_date=daily.date,
                month_day=daily.month_day,
                channel=channel.name,
                destination_id=destination_id,
                status="sent" if result.ok else "failed",
                message_hash=message_hash,
                error_message=result.error,
                sent_at=now_iso(self.timezone),
            )
        )
        return result

