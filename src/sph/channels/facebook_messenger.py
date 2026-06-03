from __future__ import annotations

from sph.channels.base import Channel
from sph.models import SendResult


class FacebookMessengerChannel(Channel):
    name = "facebook_messenger"

    async def send(self, message: str, destination_id: str | None = None) -> SendResult:
        return SendResult(
            channel=self.name,
            ok=False,
            destination_id=destination_id,
            error=(
                "Canal ainda nao ativado. Validar primeiro se a Meta permite envio "
                "automatizado para o destino pretendido e configurar token/Page/PSID."
            ),
        )

