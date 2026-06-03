from __future__ import annotations

import argparse
from datetime import date

from sph.config import settings
from sph.repository import MeditationRepository
from sph.service import DailyMeditationService


def main() -> None:
    parser = argparse.ArgumentParser(description="Ferramentas SPH Cabo Verde.")
    parser.add_argument("command", choices=["today", "preview", "day"])
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()

    service = DailyMeditationService(MeditationRepository(settings.data_path), settings.timezone)

    if args.command == "today":
        print(service.today())
    elif args.command == "preview":
        daily = service.for_date(date.fromisoformat(args.value)) if args.value else service.today()
        print(service.format_message(daily))
    elif args.command == "day":
        if not args.value:
            raise SystemExit("Informe uma data MM-DD")
        print(service.by_month_day(args.value))


if __name__ == "__main__":
    main()
