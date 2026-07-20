from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEDITATIONS_PATH = ROOT / "data" / "meditations.json"
OUTPUT_PATHS = [
    ROOT / "data" / "daily_support.json",
    ROOT / "public" / "data" / "daily_support.json",
]

SAFETY_NOTE = "Conteúdo complementar da plataforma; não é literatura oficial de NA."
CARE_NOTE = "Este apoio é complementar e não substitui técnicos de saúde, sponsor, reuniões ou emergência."


THEMES = [
    (
        "poder_superior",
        ("deus", "poder superior", "oração", "orar", "fé", "espiritual", "entregar", "render"),
    ),
    (
        "honestidade",
        ("honest", "verdade", "inventário", "admit", "defeito", "repar", "responsabilidade"),
    ),
    (
        "servico",
        ("serv", "partilhar", "ajudar", "grupo", "unidade", "companheiro", "mensagem"),
    ),
    (
        "vigilancia",
        ("vigil", "risco", "medo", "obsess", "defesa", "reserva", "velho", "impulso"),
    ),
    (
        "gratidao",
        ("gratid", "agradec", "dádiva", "alegria", "esperança", "presente"),
    ),
    (
        "relacoes",
        ("família", "amigo", "relação", "relações", "perdo", "amor", "confiança"),
    ),
]


TEMPLATES = {
    "poder_superior": {
        "standard": {
            "activity": "Reserva cinco minutos para silêncio, oração ou reflexão, e escolhe uma ação pequena que demonstre entrega hoje.",
            "phrase": "Só por hoje, posso entregar o que não controlo e cuidar do próximo passo.",
            "mental_challenge": "Quando tentares controlar tudo, pergunta: o que posso entregar e que ação honesta posso fazer agora?",
        },
        "ansioso": {
            "activity": "Lê a Oração da Serenidade devagar, respira fundo três vezes e envia uma mensagem a alguém de confiança.",
            "phrase": "A serenidade começa quando deixo de lutar sozinho.",
            "mental_challenge": "Escolhe uma preocupação para entregar por hoje e substitui-a por uma ação simples e segura.",
        },
        "risco": {
            "activity": "Antes de ficar sozinho com o impulso, liga para uma pessoa segura ou procura uma reunião agora.",
            "phrase": "Pedir ajuda é uma forma de proteção, não fraqueza.",
            "mental_challenge": "Adia qualquer decisão de risco por 20 minutos e usa esse tempo para falar com alguém.",
        },
        "consumo": {
            "activity": "Sem culpa paralisante: fala a verdade com alguém seguro e escolhe uma ação de proteção para as próximas horas.",
            "phrase": "Recomeçar com honestidade também é recuperação.",
            "mental_challenge": "Troca 'estraguei tudo' por 'preciso de ajuda agora' e dá um passo concreto.",
        },
    },
    "honestidade": {
        "standard": {
            "activity": "Escreve uma verdade simples sobre como estás hoje e partilha-a com alguém seguro.",
            "phrase": "A honestidade abre espaço para a mudança.",
            "mental_challenge": "Observa onde estás a tentar parecer forte e escolhe ser verdadeiro sem te julgar.",
        },
        "ansioso": {
            "activity": "Nomeia a ansiedade numa frase curta e partilha-a com uma pessoa que te ajude a ficar no presente.",
            "phrase": "Posso ser honesto sem me condenar.",
            "mental_challenge": "Pergunta: isto é um facto, um medo ou uma história que a minha mente está a contar?",
        },
        "risco": {
            "activity": "Diz claramente a alguém: 'estou em risco e preciso de companhia ou orientação agora'.",
            "phrase": "A verdade dita a tempo pode salvar o meu dia.",
            "mental_challenge": "Não negocies com o impulso em segredo; transforma o segredo numa chamada.",
        },
        "consumo": {
            "activity": "Faz uma partilha honesta, sem desculpas e sem autoataque, sobre o que aconteceu e o que precisas agora.",
            "phrase": "A verdade permite recomeçar com dignidade.",
            "mental_challenge": "Procura a próxima ação responsável, não uma punição para ti mesmo.",
        },
    },
    "servico": {
        "standard": {
            "activity": "Faz um gesto de serviço discreto: envia uma mensagem de força, ajuda numa reunião ou escuta alguém.",
            "phrase": "A recuperação cresce quando é partilhada.",
            "mental_challenge": "Antes de perguntar o que falta receber, pergunta que ajuda pequena podes oferecer hoje.",
        },
        "ansioso": {
            "activity": "Sai da cabeça por alguns minutos: contacta alguém para escutar, sem tentar resolver a vida inteira.",
            "phrase": "Servir também me devolve ao presente.",
            "mental_challenge": "Escolhe uma ação útil e pequena; ansiedade diminui quando o dia ganha direção.",
        },
        "risco": {
            "activity": "Procura a companhia de recuperação: grupo, reunião, sponsor ou pessoa segura antes de qualquer decisão.",
            "phrase": "Juntos, o impulso perde força.",
            "mental_challenge": "Transforma isolamento em contacto: uma mensagem agora vale mais que mil promessas depois.",
        },
        "consumo": {
            "activity": "Volta ao contacto com a comunidade; uma partilha honesta pode ser o primeiro serviço de hoje.",
            "phrase": "Não preciso desaparecer para recomeçar.",
            "mental_challenge": "Pergunta: quem pode caminhar comigo nas próximas 24 horas?",
        },
    },
    "vigilancia": {
        "standard": {
            "activity": "Identifica um sinal de risco para hoje e escolhe uma proteção concreta: reunião, descanso, chamada ou afastamento.",
            "phrase": "Vigilância é cuidado, não medo.",
            "mental_challenge": "Responde cedo ao primeiro sinal, antes que ele cresça.",
        },
        "ansioso": {
            "activity": "Reduz estímulos por dez minutos, bebe água e volta a uma ação segura já definida.",
            "phrase": "Posso proteger o meu dia com calma e clareza.",
            "mental_challenge": "Distingue perigo real de alarme interno; em ambos os casos, procura apoio seguro.",
        },
        "risco": {
            "activity": "Afasta-te imediatamente de pessoas, lugares ou objetos de risco e liga para apoio.",
            "phrase": "Hoje a minha prioridade é ficar seguro.",
            "mental_challenge": "Não proves força ficando perto do perigo; força é sair e pedir ajuda.",
        },
        "consumo": {
            "activity": "Remove o acesso ao risco nas próximas horas e combina presença com alguém seguro.",
            "phrase": "Uma recaída não precisa virar abandono.",
            "mental_challenge": "Procura o ponto exato onde podes interromper o ciclo agora.",
        },
    },
    "gratidao": {
        "standard": {
            "activity": "Escreve três coisas pequenas pelas quais podes agradecer hoje e pratica uma delas com atenção.",
            "phrase": "Gratidão ajuda-me a ver o que ainda está vivo em mim.",
            "mental_challenge": "Quando a falta aparecer, procura também uma evidência de cuidado, progresso ou esperança.",
        },
        "ansioso": {
            "activity": "Escolhe uma gratidão simples e respira com ela durante um minuto, sem forçar sentimentos.",
            "phrase": "Mesmo ansioso, posso encontrar um ponto de apoio.",
            "mental_challenge": "Procura uma coisa que esteja bem neste minuto, por menor que pareça.",
        },
        "risco": {
            "activity": "Liga para alguém e diz uma coisa pela qual ainda vale a pena proteger a tua recuperação hoje.",
            "phrase": "A vida que estou a reconstruir merece proteção.",
            "mental_challenge": "Lembra uma consequência que não queres repetir e uma razão para pedir ajuda agora.",
        },
        "consumo": {
            "activity": "Regista uma razão para continuar e procura apoio sem esperar que a vergonha passe.",
            "phrase": "Ainda posso escolher cuidado neste dia.",
            "mental_challenge": "Se a culpa falar alto, responde com uma ação de recuperação nas próximas horas.",
        },
    },
    "relacoes": {
        "standard": {
            "activity": "Escolhe uma relação para tratar com respeito hoje: ouvir, pedir desculpa, agradecer ou manter um limite saudável.",
            "phrase": "Recuperação também acontece na forma como me relaciono.",
            "mental_challenge": "Antes de reagir, pergunta: isto aproxima-me da pessoa que quero ser?",
        },
        "ansioso": {
            "activity": "Fala com alguém seguro de forma simples: 'hoje estou ansioso e preciso só ser ouvido'.",
            "phrase": "Não preciso carregar tudo em silêncio.",
            "mental_challenge": "Se a mente pedir isolamento, escolhe um contacto honesto e breve.",
        },
        "risco": {
            "activity": "Procura presença segura imediatamente; não transformes vergonha ou conflito em isolamento.",
            "phrase": "Contacto honesto pode quebrar o ciclo.",
            "mental_challenge": "Escolhe uma pessoa que proteja a tua recuperação e fala antes de agir.",
        },
        "consumo": {
            "activity": "Fala com alguém de confiança sobre o consumo e pede ajuda concreta para hoje, sem prometer sozinho.",
            "phrase": "Voltar a pedir ajuda é coragem.",
            "mental_challenge": "Se quiseres fugir das pessoas, aproxima-te de uma relação segura por um passo pequeno.",
        },
    },
    "geral": {
        "standard": {
            "activity": "Lê a meditação em voz alta e escreve uma ação pequena que podes praticar ainda hoje.",
            "phrase": "Hoje não preciso resolver a vida inteira; preciso cuidar deste dia.",
            "mental_challenge": "Quando surgir um pensamento pesado, pergunta: qual é o próximo passo honesto e seguro?",
        },
        "ansioso": {
            "activity": "Faz uma pausa de três minutos, respira devagar e escolhe apenas a próxima ação possível.",
            "phrase": "Um dia de cada vez também pode ser um minuto de cada vez.",
            "mental_challenge": "Divide o problema em uma ação pequena, segura e realista para agora.",
        },
        "risco": {
            "activity": "Sai do isolamento agora: contacta uma pessoa segura, uma reunião, sponsor ou apoio presencial.",
            "phrase": "Não preciso vencer o impulso sozinho.",
            "mental_challenge": "Antes de qualquer decisão, cria distância do risco e fala com alguém.",
        },
        "consumo": {
            "activity": "Respira, não desapareças: procura uma pessoa segura e decide o próximo passo de recuperação para hoje.",
            "phrase": "Hoje ainda pode ser um dia de verdade e recomeço.",
            "mental_challenge": "Transforma vergonha em pedido de ajuda; começa pelas próximas 24 horas.",
        },
    },
}


def detect_theme(record: dict[str, str]) -> str:
    text = " ".join(
        [
            record.get("title", ""),
            record.get("body", "")[:900],
            record.get("reflection", ""),
        ]
    ).lower()
    for theme, keywords in THEMES:
        if any(keyword in text for keyword in keywords):
            return theme
    return "geral"


def build_entry(record: dict[str, str], state: str) -> dict[str, str]:
    theme = detect_theme(record)
    template = TEMPLATES[theme][state]
    note = CARE_NOTE if state in {"risco", "consumo", "ansioso"} else SAFETY_NOTE
    return {
        "month_day": record["month_day"],
        "state": state,
        "theme": theme,
        "activity": template["activity"],
        "phrase": template["phrase"],
        "mental_challenge": template["mental_challenge"],
        "safety_note": note,
    }


def main() -> None:
    records = json.loads(MEDITATIONS_PATH.read_text(encoding="utf-8"))
    catalog = [
        build_entry(record, state)
        for record in records
        for state in ("standard", "ansioso", "risco", "consumo")
    ]

    for output_path in OUTPUT_PATHS:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"Generated {len(catalog)} support records in {len(OUTPUT_PATHS)} files.")


if __name__ == "__main__":
    main()
