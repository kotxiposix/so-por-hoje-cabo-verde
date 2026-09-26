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
VAPID_PUBLIC_KEY=...           # pode ser enviada ao browser
VAPID_PRIVATE_KEY=...          # apenas no emissor seguro
VAPID_SUBJECT=mailto:equipa@exemplo.cv
PUSH_CRON_SECRET=...           # segredo longo enviado apenas pelo agendador
ADMIN_API_SECRET=...           # protege testes e registos tecnicos
PUSH_DELIVERY_READY=false      # mudar para true so depois do teste integral
OPENAI_API_KEY=...             # apenas servidor
OPENAI_MODEL=gpt-4.1-mini
AI_DAILY_LIMIT=3               # entre 1 e 20
AI_DELIVERY_READY=false        # ativar so depois de validar conta e quota
COMMUNITY_READY=false          # manter fechada ate existir operacao de moderacao
COMMUNITY_DAILY_POST_LIMIT=3   # limite por conta e dia, entre 1 e 20
```

A URL e a chave publica podem ser usadas pelo cliente depois de as regras RLS estarem ativas. A `SERVICE_ROLE_KEY` ignora RLS e fica exclusivamente no ambiente seguro da Vercel.

O endpoint `DELETE /api/v1/account` valida o token de acesso no Supabase antes de eliminar a conta resolvida pelo servidor. Nunca aceita um `user_id` indicado pelo browser. As tabelas pessoais usam `ON DELETE CASCADE` para eliminar Jornada, preferencias e subscricoes associadas.

## 2. Modelo minimo

- `journey_state`: um documento JSON por conta; apenas o proprio utilizador pode ler e atualizar.
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

O cliente web deste repositorio ja implementa o acesso por codigo de email e a escolha explicita entre a copia local e a copia da conta. O endpoint publico `/api/v1/config` so anuncia esta funcionalidade quando URL e chave publica estiverem presentes; nunca devolve a `SERVICE_ROLE_KEY`.

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

O backend já contém os endpoints de criação pendente, listagem publicada, denúncia e moderação. O pseudónimo é gerado pelo servidor e a resposta pública nunca inclui `author_id` ou notas internas. A moderação usa `ADMIN_API_SECRET`; isto é uma base técnica, não uma área administrativa final com papéis individuais e auditoria.

Manter `COMMUNITY_READY=false` em todos os ambientes até a checklist operacional estar concluída. Com a flag desligada, a interface continua a usar apenas o diário local.

## 5. API e OpenAI na Vercel

`api/index.py` expõe a aplicacao FastAPI como funcao Python. `vercel.json` envia `/api/*` para essa funcao antes das rotas estaticas.

Variaveis privadas na Vercel:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
AI_DAILY_LIMIT=3
AI_DELIVERY_READY=false
```

Nunca colocar a chave OpenAI nem a service role do Supabase em `public/`, no Git ou em JavaScript enviado ao navegador.

O endpoint de apoio diário usa sempre o catálogo local por defeito. Só reserva e envia um pedido à OpenAI quando `AI_DELIVERY_READY=true`, a sessão da própria pessoa é validada no Supabase e a função atómica `claim_ai_daily_request` confirma que a quota diária ainda não foi atingida. A identidade da conta não é enviada à OpenAI. Falhas de autenticação, quota, rede ou fornecedor regressam silenciosamente ao catálogo local.

Os endpoints `/api/v1/admin/send-logs`, `/api/v1/admin/send-test` e `/api/v1/admin/community/*` exigem `Authorization: Bearer $ADMIN_API_SECRET`. Sem esse segredo configurado, permanecem fechados.

## 6. Checklist antes de producao

- Politica de privacidade aprovada e publicada.
- SMTP e remetente validados.
- CAPTCHA ativo no acesso por email.
- RLS testada com dois utilizadores diferentes.
- Moderadores e protocolo de crise definidos.
- Contactos de ajuda confirmados por fonte responsavel.
- Registos tecnicos sem texto sensivel das partilhas.
- Processo de exportacao e eliminacao de conta testado.
- Chaves VAPID, cron e cancelamento de subscricao push testados antes de ativar lembretes em segundo plano.

## 7. Entrega Web Push

O cliente, o registo de subscricao, as preferencias e o service worker estao preparados. A API publica so anuncia push quando conta, `VAPID_PUBLIC_KEY` e `PUSH_DELIVERY_READY=true` estiverem presentes. A chave privada nunca e devolvida ao browser.

O endpoint `POST /api/v1/internal/push/deliver` implementa a entrega e exige `Authorization: Bearer $PUSH_CRON_SECRET`. Seleciona preferencias pela hora e fuso local, evita um segundo envio no mesmo dia e desativa endpoints que respondam `404` ou `410`. A mensagem de bloqueio e generica e nao inclui dados da Jornada.

No plano Hobby, o Vercel Cron so pode executar uma vez por dia e sem precisao ao minuto. Para respeitar a hora escolhida, usar Supabase Cron (`pg_cron` + `pg_net`) para invocar este endpoint a cada minuto. Guardar o segredo no Supabase Vault. So mudar `PUSH_DELIVERY_READY=true` depois de testar subscricao, entrega, cancelamento e expiracao de endpoint em dois dispositivos.
