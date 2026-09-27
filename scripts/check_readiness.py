from __future__ import annotations

import os
from collections.abc import Mapping

from sph.public_config import public_runtime_config


def is_enabled(environment: Mapping[str, str], name: str) -> bool:
    return environment.get(name, "").strip().lower() in {"1", "true", "yes"}


def missing_values(environment: Mapping[str, str], names: tuple[str, ...]) -> list[str]:
    return [name for name in names if not environment.get(name, "").strip()]


def readiness_report(environment: Mapping[str, str] | None = None) -> dict[str, dict[str, object]]:
    env = os.environ if environment is None else environment
    public = public_runtime_config(env)["features"]
    definitions = {
        "account": (
            "ACCOUNT_READY",
            ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
        ),
        "staffAdmin": (
            "STAFF_ACCESS_READY",
            ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
        ),
        "ai": (
            "AI_DELIVERY_READY",
            (
                "SUPABASE_URL",
                "SUPABASE_PUBLISHABLE_KEY",
                "SUPABASE_SERVICE_ROLE_KEY",
                "OPENAI_API_KEY",
                "OPENAI_MODEL",
                "AI_DAILY_LIMIT",
            ),
        ),
        "push": (
            "PUSH_DELIVERY_READY",
            (
                "SUPABASE_URL",
                "SUPABASE_PUBLISHABLE_KEY",
                "SUPABASE_SERVICE_ROLE_KEY",
                "VAPID_PUBLIC_KEY",
                "VAPID_PRIVATE_KEY",
                "VAPID_SUBJECT",
                "PUSH_CRON_SECRET",
            ),
        ),
        "community": (
            "COMMUNITY_READY",
            (
                "SUPABASE_URL",
                "SUPABASE_PUBLISHABLE_KEY",
                "SUPABASE_SERVICE_ROLE_KEY",
                "STAFF_ACCESS_READY",
            ),
        ),
        "helpDirectory": (
            "HELP_DIRECTORY_READY",
            ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "STAFF_ACCESS_READY"),
        ),
        "editorialContent": (
            "EDITORIAL_CONTENT_READY",
            ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "STAFF_ACCESS_READY"),
        ),
    }
    report: dict[str, dict[str, object]] = {}
    account_flag = is_enabled(env, "ACCOUNT_READY")
    for feature, (flag, required) in definitions.items():
        missing = missing_values(env, required)
        dependencies_ready = feature in {"account", "staffAdmin", "helpDirectory", "editorialContent"} or account_flag
        report[feature] = {
            "flag": flag,
            "enabled": is_enabled(env, flag),
            "configured": not missing,
            "dependenciesReady": dependencies_ready,
            "public": bool(public.get(feature, False)),
            "missing": missing,
        }
    return report


def main() -> int:
    report = readiness_report()
    labels = {
        "account": "Conta",
        "staffAdmin": "Área da equipa",
        "ai": "AI",
        "push": "Push",
        "community": "Comunidade",
        "helpDirectory": "Diretório de ajuda",
        "editorialContent": "Conteúdo editorial",
    }
    print("Prontidão das integrações (nenhum valor secreto é mostrado):")
    for feature, status in report.items():
        state = "ATIVA" if status["public"] else "FECHADA"
        missing = ", ".join(status["missing"]) or "nenhuma variável em falta"
        print(f"- {labels[feature]}: {state}; {missing}")
    print("\nAs flags só devem ser ativadas depois dos testes operacionais da checklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
