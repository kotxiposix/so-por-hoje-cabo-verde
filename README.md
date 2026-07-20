# So Por Hoje Cabo Verde

Base tecnica inicial para publicar a meditacao diaria "So Por Hoje" a partir de uma unica fonte de verdade.

## O que esta incluido

- Dados normalizados em `data/meditations.json` e `data/meditations.csv`.
- Importador de Excel em `scripts/import_meditations.py`.
- Validador de cobertura em `scripts/validate_meditations.py`.
- API REST FastAPI em `src/sph/api.py`.
- Interface web em `public/`.
- Servicos de dominio desacoplados de canais de envio.
- Adaptadores iniciais para canal `console` e placeholder seguro para Facebook Messenger.

## Executar app

Sem dependencias externas, para testar agora:

```bash
PYTHONPATH=src python -m sph.simple_server --port 8000
```

Depois abra:

```text
http://127.0.0.1:8000/
```

## Deploy Vercel

O app esta preparado para deploy estatico na Vercel usando `public/`.

Fluxo recomendado:

```text
dev -> branch de desenvolvimento/preview
production -> branch de producao ligada a Vercel
```

Na Vercel, configure a Production Branch como `production`.

Com FastAPI:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[import,test]"
uvicorn sph.api:app --reload
```

Endpoints principais:

```text
GET /api/v1/health
GET /api/v1/today
GET /api/v1/day/{month_day}
GET /api/v1/meditations
GET /api/v1/today/preview
POST /api/v1/ai/daily-support
```

## Apoio diario com AI

Os botoes "Atividade do dia", "Frase do dia" e "Desafio mental" podem usar AI para gerar apoio complementar de acordo com a meditacao, estado do utilizador e progresso local.

Sem chave configurada, o sistema usa `data/daily_support.json`: uma base local fixa com 4 respostas para cada meditacao do ano:

- `standard`
- `ansioso`
- `risco`
- `consumo`

Para regenerar esta base local:

```bash
PYTHONPATH=src python scripts/generate_support_catalog.py
```

Para ativar OpenAI no backend local:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4.1-mini"
PYTHONPATH=src python -m sph.simple_server --port 8000
```

Na Vercel:

```text
Project Settings -> Environment Variables
OPENAI_API_KEY = sk-...
OPENAI_MODEL = gpt-4.1-mini
Redeploy
```

Implicacoes:

- A chave OpenAI fica apenas no servidor. Nunca colocar a chave no `public/app.js` ou no browser.
- Cada pedido AI pode ter custo e alguma latencia.
- O pedido envia apenas contexto minimo: titulo, excerto da meditacao, reflexao, estado local, dias limpos e sequencia de leituras.
- Nome, telefone e identidade do utilizador nao sao enviados nesta versao.
- Se a OpenAI falhar, faltar saldo, faltar internet ou nao houver chave, o sistema usa automaticamente a base local.

O conteudo gerado e complementar: nao altera a meditacao oficial e nao substitui tecnicos de saude, sponsor, reunioes ou emergencia.

## Importar novamente a planilha

```bash
python scripts/import_meditations.py "/Volumes/LENTiLHAS26/SPH Meditacões.xlsx"
python scripts/validate_meditations.py
```

## Timezone

O timezone padrao e `Atlantic/Cape_Verde`. Pode ser alterado com:

```bash
SPH_TIMEZONE=Atlantic/Cape_Verde
```

## Nota sobre Messenger

O sistema foi desenhado para manter o Facebook Messenger como um canal substituivel. A viabilidade de enviar automaticamente para um grupo existente deve ser validada com as politicas atuais da Meta antes de ativar producao.
