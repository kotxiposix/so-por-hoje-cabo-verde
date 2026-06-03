from __future__ import annotations

import json
import re
from pathlib import Path

from sph.models import Meditation


MONTH_DAY_RE = re.compile(r"^\d{2}-\d{2}$")


class MeditationRepository:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self._items: dict[str, Meditation] | None = None

    def all(self) -> list[Meditation]:
        return sorted(self._load().values(), key=lambda item: item.month_day)

    def get(self, month_day: str) -> Meditation | None:
        if not MONTH_DAY_RE.fullmatch(month_day):
            raise ValueError("month_day deve usar formato MM-DD")
        return self._load().get(month_day)

    def _load(self) -> dict[str, Meditation]:
        if self._items is not None:
            return self._items

        raw = json.loads(self.data_path.read_text(encoding="utf-8"))
        items: dict[str, Meditation] = {}
        for record in raw:
            meditation = Meditation(**record)
            if meditation.month_day in items:
                raise ValueError(f"month_day duplicado: {meditation.month_day}")
            items[meditation.month_day] = meditation

        self._items = items
        return items

