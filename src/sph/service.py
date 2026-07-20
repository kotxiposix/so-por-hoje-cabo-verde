from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sph.models import DailyMeditation, Meditation
from sph.repository import MeditationRepository


WEEKDAYS_PT = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}

MONTHS_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


class DailyMeditationService:
    def __init__(self, repository: MeditationRepository, timezone: str):
        self.repository = repository
        self.timezone = timezone

    def today(self) -> DailyMeditation:
        now = datetime.now(ZoneInfo(self.timezone)).date()
        return self.for_date(now)

    def for_date(self, target: date) -> DailyMeditation:
        month_day = target.strftime("%m-%d")
        meditation = self.repository.get(month_day)
        if meditation is None and month_day == "02-29":
            meditation = self.repository.get("02-28")
        if meditation is None:
            raise LookupError(f"Meditacao nao encontrada para {month_day}")
        return self._daily(target, meditation)

    def by_month_day(self, month_day: str) -> Meditation:
        meditation = self.repository.get(month_day)
        if meditation is None:
            raise LookupError(f"Meditacao nao encontrada para {month_day}")
        return meditation

    def format_message(self, daily: DailyMeditation) -> str:
        target = date.fromisoformat(daily.date)
        weekday = daily.weekday.replace("-feira", "")
        full_date = f"{weekday}, {target.day:02d} de {MONTHS_PT[target.month]} de {target.year}"
        header = "\n\n".join(
            [
                "BOM DIA GUERREIROS",
                "MEDITAÇÃO DO DIA",
                full_date,
            ]
        )
        body = daily.body.replace("\n\n", "\n\n\n", 1)
        return (
            f"{header}\n\n\n"
            f"{daily.title}\n\n\n"
            f"{body}\n\n\n"
            "SÓ POR HOJE:\n\n"
            f"{daily.reflection}\n\n\n"
            "soporhoje.cv\n\n\n"
            "Fonte oficial: Narcóticos Anónimos Portugal\n"
            "© NA World Services, Inc. Reprinted by permission."
        )

    def _daily(self, target: date, meditation: Meditation) -> DailyMeditation:
        return DailyMeditation(
            date=target.isoformat(),
            weekday=WEEKDAYS_PT[target.weekday()],
            month_day=meditation.month_day,
            title=meditation.title,
            body=meditation.body,
            reflection=meditation.reflection,
        )
