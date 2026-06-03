from __future__ import annotations

from sph.channels.base import Channel
from sph.models import SendResult


class ConsoleChannel(Channel):
    name = "console"

    async def send(self, message: str, destination_id: str | None = None) -> SendResult:
        print(message)
        return SendResult(channel=self.name, ok=True, destination_id=destination_id)

