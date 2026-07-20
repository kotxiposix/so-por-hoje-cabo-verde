from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from sph.config import settings
from sph.models import DailyMeditation


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
SUPPORT_CATALOG_PATH = settings.data_path.parent / "daily_support.json"


@dataclass(frozen=True)
class DailySupportRequest:
    daily: DailyMeditation
    user_state: str = ""
    clean_days: int = 0
    reading_streak: int = 0
    language: str = "pt-CV"


@dataclass(frozen=True)
class DailySupport:
    activity: str
    phrase: str
    mental_challenge: str
    safety_note: str
    source: str = "local"


SUPPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "activity": {"type": "string"},
        "phrase": {"type": "string"},
        "mental_challenge": {"type": "string"},
        "safety_note": {"type": "string"},
    },
    "required": ["activity", "phrase", "mental_challenge", "safety_note"],
}


SYSTEM_PROMPT = """
Tu és um assistente de apoio complementar à recuperação para a plataforma Só Por Hoje Cabo Verde.

Regras obrigatórias:
- Não alteres, reescrevas nem apresentes como teu o texto oficial da meditação.
- Gera apenas conteúdo complementar: atividade do dia, frase do dia e desafio mental.
- Não diagnostiques, não prometas cura e não dês conselho médico.
- Não substituis técnicos de saúde, sponsor, reuniões ou serviços de emergência.
- Usa linguagem simples, humana, sem culpa e adequada a Cabo Verde.
- Se o estado indicar risco, ansiedade forte ou consumo, orienta para ajuda real: pessoa segura, reunião, sponsor, terapeuta, centro de apoio ou emergência.
- Não peças dados pessoais.
- Mantém cada campo curto, prático e possível de fazer hoje.
- Responde apenas no JSON pedido.
""".strip()


def build_daily_support(request: DailySupportRequest) -> DailySupport:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return local_daily_support(request)

    try:
        return openai_daily_support(request, api_key)
    except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return local_daily_support(request)


def openai_daily_support(request: DailySupportRequest, api_key: str) -> DailySupport:
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "input": [
            {"role": "developer", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "meditation": {
                            "date": request.daily.date,
                            "month_day": request.daily.month_day,
                            "title": request.daily.title,
                            "body_excerpt": request.daily.body[:1200],
                            "reflection": request.daily.reflection,
                        },
                        "person_context": {
                            "state": request.user_state or "nao_informado",
                            "clean_days": request.clean_days,
                            "reading_streak": request.reading_streak,
                            "language": request.language,
                        },
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "daily_recovery_support",
                "schema": SUPPORT_SCHEMA,
                "strict": True,
            }
        },
    }
    req = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    content = extract_response_text(response_payload)
    parsed = json.loads(content)
    return DailySupport(
        activity=clean_text(parsed["activity"]),
        phrase=clean_text(parsed["phrase"]),
        mental_challenge=clean_text(parsed["mental_challenge"]),
        safety_note=clean_text(parsed["safety_note"]),
        source="openai",
    )


def extract_response_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]

    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                return content["text"]

    raise ValueError("Resposta OpenAI sem texto extraivel")


def local_daily_support(request: DailySupportRequest) -> DailySupport:
    catalog_support = catalog_daily_support(request)
    if catalog_support is not None:
        return catalog_support

    title_and_body = f"{request.daily.title} {request.daily.body}".lower()
    state = normalize_user_state(request.user_state)

    if state == "risco":
        return DailySupport(
            activity="Sai do isolamento agora: liga para uma pessoa segura ou procura uma reunião antes de ficares sozinho com o impulso.",
            phrase="Só por hoje, pedir ajuda é uma forma de proteção.",
            mental_challenge="Quando a mente disser 'eu aguento sozinho', responde com uma ação: faz uma chamada antes de decidir qualquer coisa.",
            safety_note="Este apoio não substitui ajuda profissional, sponsor, reunião ou emergência.",
        )
    if state == "consumo":
        return DailySupport(
            activity="Sem culpa paralisante: fala a verdade com alguém seguro e escolhe uma próxima ação de proteção para hoje.",
            phrase="Recomeçar hoje também faz parte da recuperação.",
            mental_challenge="Troca o pensamento 'estraguei tudo' por 'preciso de ajuda agora' e procura apoio real.",
            safety_note="Se estiveres em perigo ou sem controlo, procura ajuda presencial ou emergência.",
        )
    if state == "ansioso":
        return DailySupport(
            activity="Faz uma pausa de três minutos, lê a Oração da Serenidade e envia uma mensagem honesta a alguém de confiança.",
            phrase="Serenidade começa quando deixo de lutar sozinho.",
            mental_challenge="Identifica uma preocupação que não podes resolver agora e entrega-a por hoje, escolhendo uma ação pequena e saudável.",
            safety_note="Este apoio é complementar e não substitui acompanhamento técnico ou reunião.",
        )
    if "serv" in title_and_body:
        return DailySupport(
            activity="Faz um gesto de serviço simples e discreto, sem esperar reconhecimento.",
            phrase="Servir lembra-me que a recuperação cresce quando é partilhada.",
            mental_challenge="Antes de pensar no que falta receber, pergunta: que ajuda pequena posso oferecer hoje?",
            safety_note="Conteúdo complementar da plataforma; não é literatura oficial de NA.",
        )
    if "vigil" in title_and_body:
        return DailySupport(
            activity="Escolhe uma proteção concreta para hoje: reunião, chamada honesta, descanso ou afastar-te de um lugar de risco.",
            phrase="Vigilância é cuidado, não medo.",
            mental_challenge="Repara num sinal de risco e responde cedo, antes que ele cresça.",
            safety_note="Conteúdo complementar da plataforma; não é literatura oficial de NA.",
        )
    return DailySupport(
        activity="Lê a meditação em voz alta e escreve uma ação pequena que podes praticar ainda hoje.",
        phrase="Hoje não preciso resolver a vida inteira; preciso cuidar deste dia.",
        mental_challenge="Quando surgir um pensamento pesado, pergunta: qual é o próximo passo honesto e seguro?",
        safety_note="Conteúdo complementar da plataforma; não é literatura oficial de NA.",
    )


def catalog_daily_support(request: DailySupportRequest) -> DailySupport | None:
    catalog = load_support_catalog(SUPPORT_CATALOG_PATH)
    item = catalog.get((request.daily.month_day, normalize_user_state(request.user_state)))
    if item is None:
        item = catalog.get((request.daily.month_day, "standard"))
    if item is None:
        return None

    return DailySupport(
        activity=clean_text(item["activity"]),
        phrase=clean_text(item["phrase"]),
        mental_challenge=clean_text(item["mental_challenge"]),
        safety_note=clean_text(item["safety_note"]),
        source="catalog",
    )


@lru_cache(maxsize=4)
def load_support_catalog(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    if not path.exists():
        return {}
    records = json.loads(path.read_text(encoding="utf-8"))
    catalog: dict[tuple[str, str], dict[str, str]] = {}
    for record in records:
        month_day = str(record.get("month_day", "")).strip()
        state = normalize_user_state(str(record.get("state", "")))
        if month_day and state:
            catalog[(month_day, state)] = record
    return catalog


def normalize_user_state(value: str) -> str:
    normalized = clean_text(value).lower()
    if normalized in {"", "standard", "sem estado", "nao_informado", "não informado", "firme"}:
        return "standard"
    if normalized in {"ansiedade", "ansioso", "ansiosa"}:
        return "ansioso"
    if normalized in {"risco", "em risco"}:
        return "risco"
    if normalized in {"consumo", "consumiu", "usei", "recaida", "recaída"}:
        return "consumo"
    return normalized


def clean_text(value: str) -> str:
    return " ".join(str(value).split())


def support_to_dict(support: DailySupport) -> dict[str, str]:
    return asdict(support)
