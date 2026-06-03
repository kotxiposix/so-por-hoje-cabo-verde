from __future__ import annotations

from abc import ABC, abstractmethod

from sph.models import SendResult


class Channel(ABC):
    name: str

    @abstractmethod
    async def send(self, message: str, destination_id: str | None = None) -> SendResult:
        raise NotImplementedError

