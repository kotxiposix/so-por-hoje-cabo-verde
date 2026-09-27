# Backend seguro

Esta fase prepara conta opcional, sincronizacao da Jornada, Sala Anonima moderada e recursos de ajuda verificados. Nada aqui transforma automaticamente o prototipo local numa comunidade publica.

## 1. Criar o projeto Supabase

1. Criar um projeto e guardar a regiao escolhida.
2. No SQL Editor, rever e executar `supabase/schema.sql`.
3. Em Authentication, ativar email OTP.
4. Configurar CAPTCHA antes de permitir registos publicos.
5. Configurar SMTP proprio antes do lancamento. O envio de teste do Supabase nao serve para uma base publica de utilizadores.

Valores necessarios para a integracao:

```text
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...  # apenas servidor, nunca no browser
TURNSTILE_SITE_KEY=...         # chave publica do widget Cloudflare Turnstile
ACCOUNT_READY=false            # manter a conta escondida durante a configuracao
VAPID_PUBLIC_KEY=...           # pode ser enviada ao browser
VAPID_PRIVATE_KEY=...          # apenas no emissor seguro
VAPID_SUBJECT=mailto:equipa@exemplo.cv
PUSH_CRON_SECRET=...           # segredo longo enviado apenas pelo agendador
ADMIN_API_SECRET=...           # protege testes e registos tecnicos
STAFF_ACCESS_READY=false       # ativar só depois de atribuir e testar papéis individuais
PUSH_DELIVERY_READY=false      # mudar para true so depois do teste integral
OPENAI_API_KEY=...             # apenas servidor
OPENAI_MODEL=gpt-4.1-mini
AI_DAILY_LIMIT=3               # entre 1 e 20
AI_DELIVERY_READY=false        # ativar so depois de validar conta e quota
COMMUNITY_READY=false          # manter fechada ate existir operacao de moderacao
COMMUNITY_DAILY_POST_LIMIT=3   # limite por conta e dia, entre 1 e 20
HELP_DIRECTORY_READY=false     # usar a lista estática até validar e importar os recursos
EDITORIAL_CONTENT_READY=false  # usar os conteúdos estáticos até rever o catálogo editorial
```

A URL, a chave pública do Supabase e a site key do Turnstile só são enviadas ao cliente quando `ACCOUNT_READY=true` e todas estão presentes. A `SERVICE_ROLE_KEY` ignora RLS e fica exclusivamente no ambiente seguro da Vercel. A secret key do Turnstile é configurada apenas no Supabase e nunca entra no código ou na configuração pública da plataforma.

Para rever a configuração sem imprimir qualquer valor secreto, executar `PYTHONPATH=src python scripts/check_readiness.py`. O relatório mostra apenas se cada integração está fechada ou ativa e os nomes das variáveis ainda em falta.

Depois de executar `supabase/schema.sql`, confirmar por leitura que as tabelas e funções RPC esperadas estão expostas à chave de serviço:

```bash
PYTHONPATH=src python scripts/check_supabase_schema.py
```

O diagnóstico consulta apenas o documento OpenAPI do PostgREST, não executa funções nem altera dados. Uma aprovação neste teste não valida políticas RLS, triggers, SMTP, CAPTCHA ou isolamento entre contas; esses passos continuam a exigir os testes operacionais abaixo.

O endpoint `DELETE /api/v1/account` valida o token de acesso no Supabase antes de eliminar a conta resolvida pelo servidor. Nunca aceita um `user_id` indicado pelo browser. As tabelas pessoais usam `ON DELETE CASCADE` para eliminar Jornada, preferencias e subscricoes associadas.

## 2. Modelo minimo

- `journey_state`: um documento JSON por conta; apenas o proprio utilizador pode ler e atualizar.
- `staff_roles`: papéis mínimos da equipa; sem leitura direta pelo browser.
- `anonymous_posts`: novas partilhas entram sempre como `pending`.
- `anonymous_reports`: uma denuncia por utilizador e publicacao.
- `help_resources`: o publico ve apenas recursos marcados como verificados.
- `notification_preferences`: consentimento, hora local e fuso horario de cada conta.
- `push_subscriptions`: subscricoes Web Push pertencentes ao proprio utilizador.
- `ai_daily_usage`: contador diário por conta usado apenas para limitar pedidos OpenAI.
- `community_daily_usage`: contador diário por conta usado para proteger a fila de moderação.

O browser nao recebe permissoes para publicar diretamente, moderar, apagar mensagens de outras pessoas ou alterar recursos de ajuda. Essas operacoes pertencem a funcoes de servidor e a uma area administrativa protegida.

## 3. Migracao dos dados locais

Ao criar conta, a interface deve:

1. mostrar exatamente quais dados serao sincronizados;
2. pedir consentimento;
3. importar `sph-progress` uma unica vez;
4. manter uma copia local para funcionamento offline;
5. resolver conflitos pelo `updated_at`, oferecendo escolha quando ambos os lados mudaram.

O cliente web deste repositorio ja implementa o acesso por codigo de email e a escolha explicita entre a copia local e a copia da conta. A sincronizacao automatica compara `updated_at`; se a conta tiver mudado noutro dispositivo, pausa sem sobrescrever e volta a pedir uma escolha. A funcao SQL `save_journey_state` repete essa verificacao atomicamente no momento da escrita, fechando a janela entre leitura e gravacao. Versoes remotas superiores à suportada sao recusadas ate a aplicacao ser atualizada. O endpoint publico `/api/v1/config` so anuncia esta funcionalidade quando URL e chave publica estiverem presentes; nunca devolve a `SERVICE_ROLE_KEY`.

A pessoa pode apagar a propria linha de `journey_state` atraves da interface; a politica RLS limita o `DELETE` ao respetivo `auth.uid()`. Separadamente, pode eliminar a conta completa pelo endpoint autenticado do servidor. Esta eliminacao valida primeiro o token no Supabase e nunca confia num identificador indicado pelo browser.

Nao sincronizar texto da Sala Anonima local. Uma partilha comunitaria exige uma acao separada e explica que passara por moderacao.

## 4. Sala Anonima

Fluxo previsto:

1. utilizador autenticado escreve ate 280 caracteres;
2. cliente alerta para nao incluir nomes, contactos ou localizacao;
3. servidor cria a mensagem como `pending`;
4. moderador publica, rejeita ou oculta;
5. mensagens publicadas podem ser denunciadas;
6. conteudo que indique perigo mostra encaminhamento humano, sem simular atendimento clinico.

Antes de abrir ao publico, definir moderadores, tempos de resposta, criterios de remocao, politica de retencao e protocolo de crise.

O backend já contém os endpoints de criação pendente, listagem publicada, denúncia e moderação. O pseudónimo é gerado pelo servidor e a resposta pública nunca inclui `author_id` ou notas internas. Registos públicos malformados são omitidos. A fila administrativa assinala padrões claros de telefone, email e ligação; mensagens com esses sinais não podem ser publicadas e devem ser rejeitadas ou revistas fora da plataforma. Publicar ou rejeitar exige que a mensagem ainda esteja pendente; ocultar só aceita mensagens pendentes ou publicadas, evitando republicações acidentais. Esta deteção é apenas uma barreira de privacidade e não substitui análise humana. A moderação exige uma conta autenticada com papel `moderator` ou `admin` ativo em `staff_roles`.

Manter `COMMUNITY_READY=false` em todos os ambientes até a checklist operacional estar concluída. Com a flag desligada, a interface continua a usar apenas o diário local.

## 5. Diretório verificado de ajuda

O diretório gerido permanece desligado por `HELP_DIRECTORY_READY=false`; nesse estado, a página mostra a lista estática existente. Quando ativado, `GET /api/v1/help/resources` substitui na interface reuniões e recursos por registos verificados cuja data de revisão ainda não venceu.

A gestão de rascunhos exige `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`, mas não exige ligar `HELP_DIRECTORY_READY`. Assim, a equipa pode importar e rever recursos sem anunciar o diretório ao browser. O catálogo inicial fica em `data/help_resources_drafts.json`; `PYTHONPATH=src python scripts/import_help_resources.py` valida-o localmente e a opção explícita `--apply` cria ou atualiza os rascunhos de forma idempotente.

Criação e atualização administrativas colocam sempre o recurso em `draft`. A verificação é uma ação separada, exige fonte HTTPS e descrição, e define `review_due_at`. Recursos de emergência exigem telefone confirmado; reuniões e grupos exigem horário e pelo menos um contacto confirmado. Uma alteração posterior retira imediatamente o recurso da listagem pública até nova verificação. Registos antigos com URL, email, telefone ou formato inseguro são omitidos da resposta pública. A retirada usa o estado `retired` em vez de apagar o histórico.

Antes de ativar:

1. importar os recursos como rascunho;
2. contactar cada entidade e confirmar nome, telefone, horário e âmbito do serviço;
3. guardar a fonte responsável;
4. verificar com um prazo proporcional ao risco do contacto;
5. testar a expiração e a indisponibilidade do endpoint;
6. definir quem revê alterações e com que frequência.

## 6. API e OpenAI na Vercel

`api/index.py` expõe a aplicacao FastAPI como funcao Python. `vercel.json` envia `/api/*` para essa funcao antes das rotas estaticas.

Variaveis privadas na Vercel:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
AI_DAILY_LIMIT=3
AI_DELIVERY_READY=false
```

Nunca colocar a chave OpenAI nem a service role do Supabase em `public/`, no Git ou em JavaScript enviado ao navegador.

O endpoint de apoio diário usa sempre o catálogo local por defeito. Só reserva e envia um pedido à OpenAI quando `AI_DELIVERY_READY=true`, a sessão da própria pessoa é validada no Supabase e a função atómica `claim_ai_daily_request` confirma que a quota diária ainda não foi atingida. A meditação é resolvida novamente pela data na base canónica do servidor, por isso texto alterado no browser não entra no contexto do modelo. A identidade da conta não é enviada à OpenAI. A resposta usa esquema estrito, limites de tamanho e validação adicional para rejeitar alegações inseguras ou falta de encaminhamento humano em estados de risco. Falhas de autenticação, quota, validação, rede ou fornecedor regressam silenciosamente ao catálogo local.

Os endpoints `/api/v1/admin/community/*` exigem uma conta autenticada com papel `moderator` ou `admin`; `/api/v1/admin/help/*` exige `help_editor` ou `admin`; `/api/v1/admin/content/*` exige `content_editor` ou `admin`. A flag `STAFF_ACCESS_READY=false` mantém todos fechados mesmo quando existem contas. Os endpoints estritamente técnicos `/api/v1/admin/send-logs` e `/api/v1/admin/send-test` continuam a exigir `Authorization: Bearer $ADMIN_API_SECRET` e esse segredo não deve ser usado por pessoas no browser.

O catálogo editorial pode ser preparado em rascunho sem abrir a área pública. Depois de rever autoria, consentimento, resumo e ligações HTTPS, ativar `EDITORIAL_CONTENT_READY=true` primeiro em Preview. Qualquer edição posterior devolve o item publicado a rascunho.

Validar e importar o catálogo inicial:

```bash
PYTHONPATH=src python scripts/import_editorial_content.py
PYTHONPATH=src python scripts/import_editorial_content.py --apply
```

O segundo comando exige Supabase configurado e apenas cria ou atualiza rascunhos.

Os papéis são atribuídos diretamente no Supabase por uma pessoa administradora autorizada. A tabela não tem políticas para o browser: a aplicação resolve a sessão e consulta apenas os papéis ativos com a chave de serviço no servidor. Suspender um registo remove o acesso no pedido seguinte. Antes de ligar `STAFF_ACCESS_READY`, criar pelo menos duas contas de equipa, atribuir apenas os papéis necessários e testar que uma conta sem papel recebe `403`.

A interface da equipa está em `/admin` e não aparece na navegação pública. O login envia um código apenas para contas já existentes (`should_create_user=false`); depois, o servidor devolve somente os papéis ativos necessários para construir o espaço de trabalho. A página e os seus pedidos usam `no-store` e não entram na cache offline. O papel `admin` pode consultar um resumo sanitizado dos envios, sem destinos, conteúdo, hashes nem detalhes do fornecedor; os endpoints técnicos completos continuam protegidos por `ADMIN_API_SECRET` e não são chamados pelo browser.

As mutações editoriais feitas pelo painel incluem o identificador da conta autorizada. Triggers criam, na mesma transação, eventos mínimos em `staff_audit_events`: ação, tipo e identificador do alvo, conta responsável e data. A tabela não guarda corpo da partilha, nota de moderação, nome, telefone, email, horário nem descrição do recurso. A resposta ao browser reduz os UUID a referências curtas. Importações iniciais executadas antes de existirem contas de equipa podem criar rascunhos sem autoria; esses rascunhos devem ser revistos e verificados posteriormente no painel.

## 7. Checklist antes de producao

- Politica de privacidade aprovada e publicada.
- SMTP e remetente validados.
- CAPTCHA ativo no acesso por email.
- RLS testada com dois utilizadores diferentes.
- Moderadores e protocolo de crise definidos.
- Contactos de ajuda confirmados por fonte responsavel.
- Registos tecnicos sem texto sensivel das partilhas.
- Processo de exportacao e eliminacao de conta testado.
- Chaves VAPID, cron e cancelamento de subscricao push testados antes de ativar lembretes em segundo plano.

## 8. Entrega Web Push

O cliente, o registo de subscricao, as preferencias e o service worker estao preparados. A API publica so anuncia push quando a conta está ativa, `PUSH_DELIVERY_READY=true` e todas as variáveis de entrega estão presentes: service role, par VAPID, assunto e segredo do cron. Os valores privados nunca são devolvidos ao browser.

O endpoint `POST /api/v1/internal/push/deliver` implementa a entrega, exige `Authorization: Bearer $PUSH_CRON_SECRET` e recusa qualquer envio enquanto `PUSH_DELIVERY_READY=false`, mesmo que as restantes chaves já estejam configuradas. Seleciona preferencias pela hora e fuso local e reclama atomicamente cada entrega antes de enviar, impedindo duplicacao quando dois ciclos coincidem. A reserva expira em cinco minutos e e libertada apos falha transitoria para permitir nova tentativa. Endpoints que respondam `404` ou `410` sao desativados; se uma conta ficar sem subscricao ativa, a preferencia tambem e desligada. A mensagem de bloqueio e generica e nao inclui dados da Jornada.

No plano Hobby, o Vercel Cron so pode executar uma vez por dia e sem precisao ao minuto. Para respeitar a hora escolhida, usar Supabase Cron (`pg_cron` + `pg_net`) para invocar este endpoint a cada minuto. Guardar o segredo no Supabase Vault. So mudar `PUSH_DELIVERY_READY=true` depois de testar subscricao, entrega, cancelamento e expiracao de endpoint em dois dispositivos.
