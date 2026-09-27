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
        "account": {
            "flag": "ACCOUNT_READY",
            "values": ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "TURNSTILE_SITE_KEY"),
            "dependencies": (),
        },
        "staffAdmin": {
            "flag": "STAFF_ACCESS_READY",
            "values": ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "TURNSTILE_SITE_KEY"),
            "dependencies": (),
        },
        "ai": {
            "flag": "AI_DELIVERY_READY",
            "values": (
                "SUPABASE_URL",
                "SUPABASE_PUBLISHABLE_KEY",
                "SUPABASE_SERVICE_ROLE_KEY",
                "TURNSTILE_SITE_KEY",
                "OPENAI_API_KEY",
                "OPENAI_MODEL",
                "AI_DAILY_LIMIT",
            ),
            "dependencies": ("ACCOUNT_READY",),
        },
        "push": {
            "flag": "PUSH_DELIVERY_READY",
            "values": (
                "SUPABASE_URL",
                "SUPABASE_PUBLISHABLE_KEY",
                "SUPABASE_SERVICE_ROLE_KEY",
                "TURNSTILE_SITE_KEY",
                "VAPID_PUBLIC_KEY",
                "VAPID_PRIVATE_KEY",
                "VAPID_SUBJECT",
                "PUSH_CRON_SECRET",
            ),
            "dependencies": ("ACCOUNT_READY",),
        },
        "community": {
            "flag": "COMMUNITY_READY",
            "values": (
                "SUPABASE_URL",
                "SUPABASE_PUBLISHABLE_KEY",
                "SUPABASE_SERVICE_ROLE_KEY",
                "TURNSTILE_SITE_KEY",
            ),
            "dependencies": ("ACCOUNT_READY", "STAFF_ACCESS_READY"),
        },
        "helpDirectory": {
            "flag": "HELP_DIRECTORY_READY",
            "values": ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "TURNSTILE_SITE_KEY"),
            "dependencies": ("STAFF_ACCESS_READY",),
        },
        "editorialContent": {
            "flag": "EDITORIAL_CONTENT_READY",
            "values": ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "TURNSTILE_SITE_KEY"),
            "dependencies": ("STAFF_ACCESS_READY",),
        },
    }
    report: dict[str, dict[str, object]] = {}
    for feature, definition in definitions.items():
        flag = str(definition["flag"])
        missing = missing_values(env, definition["values"])
        disabled_dependencies = [
            name for name in definition["dependencies"] if not is_enabled(env, name)
        ]
        dependencies_ready = not disabled_dependencies
        report[feature] = {
            "flag": flag,
            "enabled": is_enabled(env, flag),
            "configured": not missing and dependencies_ready,
            "dependenciesReady": dependencies_ready,
            "disabledDependencies": disabled_dependencies,
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
        dependencies = ", ".join(status["disabledDependencies"])
        dependency_note = f"; dependências fechadas: {dependencies}" if dependencies else ""
        print(f"- {labels[feature]}: {state}; {missing}{dependency_note}")
    print("\nAs flags só devem ser ativadas depois dos testes operacionais da checklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
