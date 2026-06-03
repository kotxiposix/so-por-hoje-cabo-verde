from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sph.channels.base import Channel
from sph.sender import DailySender


async def run_daily_loop(
    sender: DailySender,
    channel: Channel,
    hour: int,
    minute: int,
    destination_id: str | None = None,
) -> None:
    while True:
        now = datetime.now(ZoneInfo(sender.timezone))
        if now.hour == hour and now.minute == minute:
            await sender.send_for_date(now.date(), channel, destination_id=destination_id)
            await asyncio.sleep(60)
        await asyncio.sleep(20)

