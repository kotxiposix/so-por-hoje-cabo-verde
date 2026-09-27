from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


EXPECTED_OBJECTS: dict[str, tuple[str, ...]] = {
    "account": (
        "/journey_state",
        "/rpc/save_journey_state",
    ),
    "staffAdmin": (
        "/staff_roles",
        "/staff_audit_events",
    ),
    "ai": (
        "/ai_daily_usage",
        "/rpc/claim_ai_daily_request",
    ),
    "push": (
        "/notification_preferences",
        "/push_subscriptions",
        "/rpc/claim_push_delivery",
        "/rpc/complete_push_delivery",
        "/rpc/release_push_delivery",
    ),
    "community": (
        "/anonymous_posts",
        "/anonymous_reports",
        "/community_daily_usage",
        "/rpc/submit_anonymous_post",
    ),
    "helpDirectory": ("/help_resources",),
    "editorialContent": ("/editorial_content",),
}

LABELS = {
    "account": "Conta e Jornada",
    "staffAdmin": "Área da equipa",
    "ai": "Apoio diário com AI",
    "push": "Notificações push",
    "community": "Comunidade moderada",
    "helpDirectory": "Diretório de ajuda",
    "editorialContent": "Conteúdo editorial",
}


@dataclass(frozen=True)
class SchemaProbe:
    configured: bool
    reachable: bool
    features: dict[str, dict[str, object]]
    error: str | None = None


def _empty_features() -> dict[str, dict[str, object]]:
    return {
        feature: {
            "complete": False,
            "present": [],
            "missing": list(objects),
        }
        for feature, objects in EXPECTED_OBJECTS.items()
    }


def inspect_openapi_schema(document: Mapping[str, Any]) -> dict[str, dict[str, object]]:
    raw_paths = document.get("paths", {})
    paths = set(raw_paths) if isinstance(raw_paths, Mapping) else set()
    report: dict[str, dict[str, object]] = {}
    for feature, expected in EXPECTED_OBJECTS.items():
        present = [path for path in expected if path in paths]
        missing = [path for path in expected if path not in paths]
        report[feature] = {
            "complete": not missing,
            "present": present,
            "missing": missing,
        }
    return report


def fetch_openapi_schema(
    supabase_url: str,
    service_role_key: str,
    opener: Callable[..., Any] = urlopen,
) -> Mapping[str, Any]:
    request = Request(
        f"{supabase_url.rstrip('/')}/rest/v1/",
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Accept": "application/openapi+json",
            "Accept-Profile": "public",
        },
    )
    with opener(request, timeout=15) as response:
        document = json.loads(response.read().decode("utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError("invalid_openapi_document")
    return document


def probe_supabase_schema(
    environment: Mapping[str, str] | None = None,
    opener: Callable[..., Any] = urlopen,
) -> SchemaProbe:
    env = os.environ if environment is None else environment
    supabase_url = env.get("SUPABASE_URL", "").strip()
    service_role_key = env.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not service_role_key:
        return SchemaProbe(False, False, _empty_features(), "missing_configuration")
    if not supabase_url.startswith("https://"):
        return SchemaProbe(True, False, _empty_features(), "invalid_supabase_url")

    try:
        document = fetch_openapi_schema(supabase_url, service_role_key, opener)
    except HTTPError as exc:
        return SchemaProbe(True, False, _empty_features(), f"http_{exc.code}")
    except (URLError, TimeoutError):
        return SchemaProbe(True, False, _empty_features(), "connection_failed")
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return SchemaProbe(True, False, _empty_features(), "invalid_response")

    return SchemaProbe(True, True, inspect_openapi_schema(document))


def main() -> int:
    probe = probe_supabase_schema()
    print("Verificação do esquema Supabase (somente leitura; nenhum segredo é mostrado):")
    if not probe.configured:
        print("- NÃO EXECUTADA: faltam SUPABASE_URL e/ou SUPABASE_SERVICE_ROLE_KEY.")
        return 2
    if not probe.reachable:
        print(f"- NÃO CONCLUÍDA: {probe.error}.")
        return 2

    complete = True
    for feature, status in probe.features.items():
        if status["complete"]:
            print(f"- {LABELS[feature]}: esquema presente")
            continue
        complete = False
        missing = ", ".join(status["missing"])
        print(f"- {LABELS[feature]}: incompleto; faltam {missing}")

    print("\nEsta verificação confirma exposição das tabelas e RPCs esperadas; não substitui testes de RLS, triggers ou fluxos com contas reais.")
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
