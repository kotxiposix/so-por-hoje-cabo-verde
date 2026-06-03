from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    data_path: Path = ROOT / "data" / "meditations.json"
    send_log_path: Path = ROOT / "data" / "send_logs.jsonl"
    timezone: str = os.getenv("SPH_TIMEZONE", "Atlantic/Cape_Verde")
    default_send_hour: int = int(os.getenv("SPH_SEND_HOUR", "7"))
    default_send_minute: int = int(os.getenv("SPH_SEND_MINUTE", "0"))


settings = Settings()
