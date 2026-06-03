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
```

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
