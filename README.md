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

O app usa `public/` para a interface estatica e `api/index.py` para disponibilizar a API FastAPI como funcao Python na Vercel.

Fluxo recomendado:

```text
dev -> branch de desenvolvimento/preview
production -> branch de producao ligada a Vercel
```

Na Vercel, configure a Production Branch como `production`. O workflow GitHub valida `dev`, `production` e pull requests; nao publica uma copia estatica no GitHub Pages, porque essa copia nao suportaria a API.

As instrucoes para conta, sincronizacao e comunidade moderada estao em `docs/BACKEND_SETUP.md`. A sequencia operacional esta em `docs/ACTIVATION_CHECKLIST.md` e o esquema inicial em `supabase/schema.sql`.

## PWA e dados locais

A interface principal inclui manifesto e service worker. Quando servida por `localhost` ou HTTPS, pode ser instalada e mantem o essencial disponivel parcialmente offline:

- interface principal;
- base das meditacoes;
- catalogo de apoio complementar;
- icones e estilos essenciais.

Sem rede, atividade, frase e desafio continuam a usar a entrada do catálogo correspondente ao dia e ao check-in escolhido. Quando existe uma nova versão do service worker, a área Mais mostra uma ação explícita para atualizar, evitando uma recarga inesperada durante a utilização.

Jornada, gratidoes, check-ins, plano pessoal e Sala Anonima usam `localStorage`. A pessoa pode exportar uma copia JSON versionada e voltar a importa-la no mesmo ou noutro dispositivo. A importacao aceita ficheiros ate 1 MB, valida a versao, datas e campos permitidos e pede confirmacao antes de substituir os dados locais.

O cliente de conta opcional esta preparado para Supabase Email OTP. So fica visivel quando `ACCOUNT_READY=true`, `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY` estiverem configurados. A sincronizacao exige uma escolha explicita entre a copia local e a copia da conta; a Sala Anonima local e as preferencias de notificacao nunca entram nessa sincronizacao.

Abrir `public/index.html` diretamente com `file://` serve apenas para inspecao visual. API, PWA, cache offline e alguns recursos do navegador exigem o servidor local:

```bash
PYTHONPATH=src python3 -m sph.simple_server --port 8000
```

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
GET /api/v1/config
GET /api/v1/today
GET /api/v1/day/{month_day}
GET /api/v1/meditations
GET /api/v1/today/preview
POST /api/v1/ai/daily-support
GET /api/v1/community/posts
POST /api/v1/community/posts
POST /api/v1/community/posts/{post_id}/reports
GET /api/v1/help/resources
DELETE /api/v1/account
POST /api/v1/internal/push/deliver
```

Publicação e denúncia na comunidade exigem a sessão da própria pessoa e só funcionam quando `COMMUNITY_READY=true`. A eliminação exige a mesma validação de sessão e a entrega push exige o segredo do agendador.

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

O servidor simples mantém sempre o catálogo local. Para testar a integração OpenAI com os mesmos controlos usados em produção, use FastAPI, uma conta Supabase válida e o esquema atualizado:

```bash
export SUPABASE_URL="https://PROJECT_REF.supabase.co"
export SUPABASE_PUBLISHABLE_KEY="..."
export ACCOUNT_READY="true"
export SUPABASE_SERVICE_ROLE_KEY="..."
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4.1-mini"
export AI_DAILY_LIMIT="3"
export AI_DELIVERY_READY="true"
uvicorn sph.api:app --reload
```

Usar este bloco apenas num ambiente de teste onde RLS, Email OTP, SMTP e CAPTCHA ja tenham sido validados. Fora desse ensaio controlado, manter `ACCOUNT_READY=false` e `AI_DELIVERY_READY=false`.

Na Vercel:

```text
Project Settings -> Environment Variables
OPENAI_API_KEY = sk-...
OPENAI_MODEL = gpt-4.1-mini
AI_DAILY_LIMIT = 3
AI_DELIVERY_READY = false
Redeploy
```

Manter `AI_DELIVERY_READY=false` até executar `supabase/schema.sql`, validar o acesso por email e testar a quota. Depois do teste integral, mudar para `true` primeiro em Preview. Pessoas sem conta continuam a receber o catálogo local.

O estado das integrações pode ser auditado sem revelar valores com:

```bash
PYTHONPATH=src python scripts/check_readiness.py
```

Implicacoes:

- A chave OpenAI fica apenas no servidor. Nunca colocar a chave no `public/app.js` ou no browser.
- Cada pedido AI pode ter custo e alguma latencia.
- A OpenAI só é chamada para uma conta autenticada e dentro do limite diário configurado; o limite é reclamado atomicamente no servidor.
- O pedido envia apenas contexto minimo: titulo, excerto da meditacao, reflexao, estado local, dias limpos e sequencia de leituras.
- Nome, email, telefone e identificador da conta nao sao enviados à OpenAI nesta versao.
- O Supabase guarda por conta apenas a data e o número de utilizações AI necessárias para aplicar a quota.
- Se a OpenAI falhar, faltar saldo, faltar internet ou nao houver chave, o sistema usa automaticamente a base local.

O conteudo gerado e complementar: nao altera a meditacao oficial e nao substitui tecnicos de saude, sponsor, reunioes ou emergencia.

## Sala Anónima moderada

O backend da futura comunidade está preparado, mas permanece fechado por defeito. Quando `COMMUNITY_READY=false`, os endpoints devolvem indisponível e a interface mantém a Sala Anónima apenas no dispositivo.

Quando a equipa concluir as decisões operacionais e ativar a flag, o servidor:

- valida a conta sem confiar num identificador enviado pelo browser;
- gera um pseudónimo novo no servidor;
- cria todas as partilhas como `pending`;
- aplica um limite diário atómico por conta, configurado por `COMMUNITY_DAILY_POST_LIMIT`;
- expõe publicamente apenas `id`, pseudónimo, texto e data de mensagens publicadas;
- valida novamente cada registo antes de o expor e omite linhas malformadas;
- aceita uma denúncia por conta e publicação;
- reserva publicação, rejeição e ocultação para endpoints administrativos protegidos;
- assinala telefones, emails e ligações na fila e bloqueia a respetiva publicação;
- impede republicar silenciosamente mensagens já rejeitadas ou ocultadas.

Esta preparação não substitui moderadores, regras editoriais, retenção, horário de resposta nem protocolo de crise.

## Diretório verificado de ajuda

A página mantém os contactos estáticos enquanto `HELP_DIRECTORY_READY=false`. O backend gerido e a substituição automática na interface já estão preparados para uma ativação posterior.

No fluxo gerido:

- recursos novos ou alterados ficam sempre em `draft` e invisíveis ao público;
- a verificação exige uma fonte URL e define uma data máxima para nova revisão;
- recursos cuja revisão venceu deixam automaticamente de aparecer;
- o endpoint público devolve apenas campos necessários para apresentar e contactar o recurso;
- retirar um recurso muda-o para `retired`, preservando o histórico em vez de o apagar;
- gestão, verificação e retirada exigem uma sessão de equipa com o papel `help_editor` ou `admin`.

Não ativar o diretório sem rever os contactos, horários e fontes diretamente com as entidades responsáveis.

## Importar novamente a planilha

```bash
python scripts/import_meditations.py "/Volumes/LENTiLHAS26/SPH Meditacões.xlsx"
PYTHONPATH=src python scripts/generate_support_catalog.py
python scripts/validate_meditations.py
```

O importador atualiza a base canónica em `data/` e a cópia servida pela aplicação em `public/data/`. Regenera depois o catálogo de apoio diário para manter atividade, frase e desafio alinhados com a meditação atualizada. A suíte de testes recusa cópias divergentes.

## Timezone

O timezone padrao e `Atlantic/Cape_Verde`. Pode ser alterado com:

```bash
SPH_TIMEZONE=Atlantic/Cape_Verde
```

## Nota sobre Messenger

O sistema foi desenhado para manter o Facebook Messenger como um canal substituivel. A viabilidade de enviar automaticamente para um grupo existente deve ser validada com as politicas atuais da Meta antes de ativar producao.
