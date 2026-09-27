# Arquitetura da plataforma

Este documento descreve a arquitetura implementada da plataforma So Por Hoje Cabo Verde. A referencia funcional e de ativacao permanece em `docs/ACTIVATION_CHECKLIST.md`.

## 1. Visao geral

```text
                         +----------------------+
                         |  Navegador / PWA     |
                         |  public/index.html   |
                         +----------+-----------+
                                    |
                  catalogo local    | API /api/v1
                +-------------------+-------------------+
                |                                       |
                v                                       v
     public/data/meditations.json             FastAPI em src/sph/api.py
     public/data/daily-support.json                       |
                |                          +--------------+--------------+
                |                          |              |              |
                v                          v              v              v
       experiencia offline              Supabase       OpenAI        Web Push
       e fallback seguro             conta/dados    apoio diario    entrega
```

A aplicacao funciona primeiro com dados locais. Conta, sincronizacao, AI, notificacoes push, diretorio gerido e comunidade publica sao integracoes opcionais, fechadas por defeito e ativadas separadamente.

## 2. Superficies publicas

- `/`: aplicacao principal com Meditacao, Jornada, Viver Saudavel, Ajuda e Sobre.
- `/expo`: pagina publica da exposicao fotografica.
- `/privacidade`: politica e explicacao sobre dados.
- `/api/v1/*`: API JSON com respostas `no-store`.
- `sw.js`: instalacao, cache offline e rececao de notificacoes genericas.

A navegacao principal fica no fundo em ecras moveis e mantem espaco reservado para nao tapar o conteudo. No desktop continua acessivel sem transformar a aplicacao numa pagina promocional.

## 3. Fonte unica da meditacao

```text
data/meditations.json
          |
          | scripts/import_meditations.py
          v
public/data/meditations.json
          |
          +--> aplicacao e PWA offline
          +--> API diaria
          +--> formatacao de partilha
```

Regras:

- `month_day` (`MM-DD`) e a chave canonica.
- O ano pertence apenas a data de apresentacao ou envio.
- O texto oficial nao e reescrito pela AI.
- Os testes recusam divergencia entre a base canonica e a copia publica.
- Atividade, frase e desafio sao conteudo complementar e vivem num catalogo separado.

## 4. Dados da Jornada

Sem conta, os dados pessoais permanecem no dispositivo em `localStorage`:

- data de sobriedade;
- leituras e sequencias;
- check-in diario;
- gratidoes e plano pessoal;
- preferencias e marcos.

A pessoa pode exportar e importar uma copia JSON versionada. A importacao valida tamanho, versao, datas e campos permitidos antes de substituir os dados.

Com conta ativa, o cliente usa Supabase Email OTP. A sincronizacao e explicita: a pessoa escolhe qual copia conservar quando existe conflito. Campos exclusivos do dispositivo, incluindo a Sala Anonima local e preferencias de notificacao, nao entram na copia da Jornada. Quando o push real e escolhido, hora, fuso e subscricao tecnica usam um registo separado no servidor.

## 5. Backend e integracoes

### Conta e Supabase

`ACCOUNT_READY=true` so expoe a conta quando URL, chave publica e `TURNSTILE_SITE_KEY` tambem existem. O mesmo bloqueio protege o login da equipa. O token Turnstile de uso unico segue para o endpoint OTP do Supabase, que valida o desafio com a chave secreta configurada no painel. Operacoes privilegiadas usam `SUPABASE_SERVICE_ROLE_KEY` apenas no servidor. As politicas RLS continuam a ser a defesa principal para acesso por utilizador.

### Apoio diario com AI

`AI_DELIVERY_READY=true` requer conta ativa, sessao valida, chave OpenAI, modelo, limite diario e service role. A quota e reclamada atomicamente antes da chamada. Qualquer falha regressa ao catalogo local, sem impedir o uso da aplicacao.

### Web Push

`PUSH_DELIVERY_READY=true` so anuncia a funcionalidade ao browser quando todo o caminho de entrega esta configurado: conta, service role, par VAPID, assunto e segredo do cron. O service worker ignora titulo e corpo remotos e apresenta uma mensagem generica, reduzindo exposicao no ecra bloqueado.

### Diretorio de ajuda

O catalogo estatico continua disponivel enquanto `HELP_DIRECTORY_READY=false`. O diretorio gerido aceita importacao administrativa de rascunhos, mas so publica recursos verificados e dentro do prazo de revisao.

### Conteúdo editorial

`EDITORIAL_CONTENT_READY=false` mantém o catálogo gerido invisível e preserva os conteúdos estáticos de Viver Saudável. O papel `content_editor` pode preparar rascunhos no painel; título, resumo e ligação HTTPS são obrigatórios antes da publicação. Editar um item publicado devolve-o automaticamente a rascunho, e publicação ou retirada fica registada na auditoria privada.

### Comunidade

`COMMUNITY_READY=false` mantem a Sala Anonima publica indisponivel. O prototipo local nao simula conversa real. O backend preparado recebe partilhas como pendentes e exige moderacao antes de qualquer publicacao.

Quando a flag está ativa, o cliente lê apenas publicações aprovadas. Enviar ou denunciar exige uma sessão válida; novas partilhas nunca aparecem diretamente e entram primeiro na fila de moderação. O conteúdo comunitário é construído com `textContent`, sem interpolação de HTML.

As ações editoriais usam papéis individuais guardados em `staff_roles`: `moderator` para a comunidade, `help_editor` para o diretório e `admin` para ambas. `STAFF_ACCESS_READY=false` mantém estes acessos fechados até existirem contas reais testadas; `ADMIN_API_SECRET` fica reservado aos endpoints técnicos internos.

O painel `/admin` é uma superfície operacional separada da aplicação pública. Não é apresentado no menu, não é indexável nem guardado pelo service worker. A interface pede autenticação individual, consulta `/api/v1/admin/me` e mostra apenas as ferramentas permitidas pelos papéis ativos. A vista de operação, exclusiva de `admin`, recebe apenas data, canal, estado e hora dos envios; identificadores de destino, conteúdo, hashes e erros brutos permanecem no lado do servidor.

As decisões editoriais usam autoria mínima nas tabelas de origem e triggers PostgreSQL para inserir `staff_audit_events` atomicamente. O evento contém apenas ação, alvo técnico, conta e data; a API administrativa ainda abrevia os identificadores antes de os enviar ao browser. A tabela de auditoria tem RLS sem política direta e as funções de trigger não são executáveis por `anon` ou `authenticated`.

## 6. Portoes de ativacao

```text
ACCOUNT_READY
    +--> conta e sincronizacao
    +--> AI_DELIVERY_READY
    +--> PUSH_DELIVERY_READY
    +--> COMMUNITY_READY + STAFF_ACCESS_READY

HELP_DIRECTORY_READY + STAFF_ACCESS_READY
    +--> diretório verificado, independente da conta pública

EDITORIAL_CONTENT_READY + STAFF_ACCESS_READY
    +--> catálogo editorial, independente da conta pública
```

As flags nao substituem as credenciais nem os testes operacionais. A API publica so anuncia uma funcionalidade quando a flag, as dependencias e todas as variaveis obrigatorias estao presentes.

Auditoria segura das variáveis e flags:

```bash
PYTHONPATH=src python scripts/check_readiness.py
```

O comando mostra estados e nomes de variaveis em falta, nunca valores.

Depois de aplicar `supabase/schema.sql`, a estrutura remota pode ser verificada por leitura, sem executar RPCs nem escrever dados:

```bash
PYTHONPATH=src python scripts/check_supabase_schema.py
```

O mapa requisito a requisito está em `docs/IMPLEMENTATION_MATRIX.md`.

## 7. Seguranca e privacidade

- Segredos nunca entram em `public/`, respostas publicas ou logs.
- Check-ins, gratidoes, partilhas e conteudo privado da Jornada nao sao registados em logs da aplicacao.
- Eliminacao de conta resolve a identidade a partir do token autenticado, nunca de um `user_id` enviado pelo browser.
- Endpoints internos exigem segredos proprios e independentes.
- A politica CSP restringe scripts, ligacoes e embeds externos.
- Push mostra conteudo generico e aceita apenas rotas da mesma origem.
- Dados comunitarios publicos usam pseudonimo criado no servidor e omitem identidade.
- Loja, doacao e comunidade nao sao ativadas sem operacao e responsaveis definidos.

## 8. PWA e funcionamento offline

O service worker mantem um cache versionado da interface, meditacoes e apoio diario. Atualizacoes exigem acao explicita para evitar trocar a aplicacao durante uma leitura. Ao regressar a app depois da meia-noite, o cliente atualiza a data e carrega a nova meditacao.

Ha fallbacks separados para aplicacao, exposicao e privacidade. A instalacao apresenta instrucoes adequadas a iPhone/iPad, Android ou desktop quando o navegador nao fornece um prompt automatico.

## 9. Verificacao

A suite cobre:

- dominio e API Python;
- cliente de conta e sincronizacao;
- aritmetica de datas e sequencias;
- exportacao/importacao da Jornada;
- apoio offline e fallbacks da AI;
- portoes publicos e entrega push;
- diretorio de ajuda e importadores;
- estrutura web, headers e PWA.

Comandos locais:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.mjs
git diff --check
```

## 10. Publicacao

- `dev`: desenvolvimento e Preview.
- `production`: ramo de producao na Vercel.
- GitHub Pages nao e usado porque nao executa a API.
- Cada integracao deve ser validada primeiro em Preview.
- Producao so recebe a mesma configuracao depois do roteiro manual e automatico completo.

O deploy do frontend nao ativa automaticamente servicos sensiveis. As flags permanecem falsas ate a equipa concluir os passos humanos e operacionais da checklist.
