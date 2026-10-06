from __future__ import annotations

import base64
import os
import re
from collections.abc import Mapping
from collections.abc import Callable

from sph.public_config import public_runtime_config


def is_enabled(environment: Mapping[str, str], name: str) -> bool:
    return environment.get(name, "").strip().lower() in {"1", "true", "yes"}


def missing_values(environment: Mapping[str, str], names: tuple[str, ...]) -> list[str]:
    return [name for name in names if not environment.get(name, "").strip()]


def valid_vapid_public_key(value: str) -> bool:
    try:
        padding = "=" * (-len(value) % 4)
        decoded = base64.urlsafe_b64decode(value + padding)
    except (ValueError, TypeError):
        return False
    return len(decoded) == 65 and decoded[0] == 4


def valid_vapid_private_key(value: str) -> bool:
    stripped = value.strip()
    return (
        stripped.startswith("-----BEGIN PRIVATE KEY-----")
        and stripped.endswith("-----END PRIVATE KEY-----")
        and len(stripped) >= 120
    )


def valid_vapid_subject(value: str) -> bool:
    stripped = value.strip()
    if stripped.startswith("mailto:"):
        email = stripped.removeprefix("mailto:")
        return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))
    return bool(re.fullmatch(r"https://[^\s/]+(?:/[^\s]*)?", stripped))


def valid_secret(value: str) -> bool:
    stripped = value.strip()
    return len(stripped) >= 32 and not any(character.isspace() for character in stripped)


def valid_ai_daily_limit(value: str) -> bool:
    try:
        return 1 <= int(value.strip()) <= 20
    except ValueError:
        return False


def valid_model_name(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{1,99}", value.strip()))


def invalid_values(
    environment: Mapping[str, str],
    validators: Mapping[str, Callable[[str], bool]],
) -> list[str]:
    return [
        name
        for name, validator in validators.items()
        if environment.get(name, "").strip() and not validator(environment[name])
    ]


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
            "validators": {
                "OPENAI_MODEL": valid_model_name,
                "AI_DAILY_LIMIT": valid_ai_daily_limit,
            },
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
            "validators": {
                "VAPID_PUBLIC_KEY": valid_vapid_public_key,
                "VAPID_PRIVATE_KEY": valid_vapid_private_key,
                "VAPID_SUBJECT": valid_vapid_subject,
                "PUSH_CRON_SECRET": valid_secret,
            },
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
        invalid = invalid_values(env, definition.get("validators", {}))
        disabled_dependencies = [
            name for name in definition["dependencies"] if not is_enabled(env, name)
        ]
        dependencies_ready = not disabled_dependencies
        report[feature] = {
            "flag": flag,
            "enabled": is_enabled(env, flag),
            "configured": not missing and not invalid and dependencies_ready,
            "dependenciesReady": dependencies_ready,
            "disabledDependencies": disabled_dependencies,
            "public": bool(public.get(feature, False)),
            "missing": missing,
            "invalid": invalid,
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
        invalid = ", ".join(status["invalid"])
        dependencies = ", ".join(status["disabledDependencies"])
        dependency_note = f"; dependências fechadas: {dependencies}" if dependencies else ""
        invalid_note = f"; formato inválido: {invalid}" if invalid else ""
        print(f"- {labels[feature]}: {state}; {missing}{invalid_note}{dependency_note}")
    print("\nAs flags só devem ser ativadas depois dos testes operacionais da checklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
