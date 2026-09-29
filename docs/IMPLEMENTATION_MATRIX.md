# Matriz de implementação da plataforma

Esta matriz traduz o mapa funcional da plataforma em estado técnico, porta de ativação, evidência e próxima decisão. Deve ser lida em conjunto com `docs/ACTIVATION_CHECKLIST.md`: uma função tecnicamente preparada não está automaticamente autorizada para uso público.

## Estados

- **Ativa localmente**: funciona sem serviço externo e está disponível na aplicação.
- **Preparada e fechada**: código e testes existem, mas uma flag mantém a função indisponível.
- **Depende da equipa**: exige validação operacional, conteúdo confirmado ou teste em dispositivos reais.
- **Não iniciada**: ainda não existe um fluxo seguro e completo, por decisão explícita.

## Navegação principal

| Área | Estado | Implementação e proteção | Próximo passo |
| --- | --- | --- | --- |
| Meditação | Ativa localmente | Meditação canónica diária, reflexão, atividade, frase, desafio, gratidão, histórico e partilha; funciona offline | Rever periodicamente conteúdo complementar e permissão da fonte oficial |
| Jornada | Ativa localmente e sincronizável | Dias limpos, check-in, histórico, marcos, plano pessoal e backup JSON ficam no dispositivo; a conta permite sincronização opcional | Monitorizar a sincronização e manter testes de regressão com duas contas |
| Viver Saudável | Ativa localmente | Podcast e vídeos sob escolha explícita, história, exposição e recursos estáticos; ligações editoriais são revalidadas no navegador | Rever e publicar o catálogo gerido antes de ativar `EDITORIAL_CONTENT_READY` |
| Ajuda | Ativa localmente | SOS, orientação de risco, 17 recursos locais e acesso acionável; falha ou resposta vazia do diretório preserva o fallback e os links são revalidados no navegador | Confirmar contactos/horários e testar o diretório gerido antes de ativar `HELP_DIRECTORY_READY` |
| Sobre | Ativa localmente | Missão, visão, história, equipa, privacidade, contacto e FAQ | Concluir revisão jurídica e confirmar parceiros antes de os identificar publicamente |

A navegação principal é fixa no fundo em ecrãs pequenos. O conteúdo reserva espaço para que a barra não cubra ações ou texto. Setas, Home e End percorrem o menu sem ativação acidental; Enter abre a área e uma região viva anuncia a mudança. Um atalho de teclado permite saltar diretamente para o conteúdo. Um contrato automatizado confirma as cinco áreas, os controlos essenciais, os três apoios diários e os quatro estados de check-in previstos neste mapa.

## Conta, dados e experiência instalada

| Capacidade | Estado | Porta ou limite | Evidência |
| --- | --- | --- | --- |
| Conta por código de email | Ativa em produção | `ACCOUNT_READY=true`; Supabase, OTP, SMTP e CAPTCHA validados com endereços Gmail e Hotmail | `public/account-client.mjs`, `/api/v1/config` |
| Sincronização da Jornada | Ativa em produção | Escolha explícita entre cópia local e remota; allowlist de campos; preferências do dispositivo preservadas; cursor por conta deteta alteração ou eliminação remota; RLS por conta | `save_journey_state`, testes de conflito, cursor e versão |
| Eliminação de dados e conta | Ativa em produção | Sessão validada no servidor; nunca aceita `user_id` do browser | `DELETE /api/v1/account`, RLS e `ON DELETE CASCADE` |
| PWA e offline parcial | Ativa localmente | Manifesto com ícones 192/512; instalação e atualização final dependem do navegador/dispositivo | `manifest.webmanifest`, `sw.js`, `docs/PWA_DEVICE_TEST.md` |
| Notificações dentro da app | Ativa localmente | Preferência guardada no dispositivo | Cliente principal |
| Web Push real | Preparada e fechada | `PUSH_DELIVERY_READY`; reconcilia permissão, escolha local, sessão e subscrição; VAPID, cron e teste em dois dispositivos | emissor protegido, reserva atómica e service worker |

## Conteúdo personalizado e editorial

| Capacidade | Estado | Porta ou limite | Evidência |
| --- | --- | --- | --- |
| Atividade, frase e desafio locais | Ativa localmente | 366 dias × 4 estados, contexto pelo título, diversidade mínima e fallback obrigatório | `public/data/daily_support.json` e testes de seleção/qualidade |
| Apoio diário com AI | Preparada e fechada | `AI_DELIVERY_READY`; conta, quota, OpenAI e revisão de custos | `/api/v1/ai/daily-support`, validação e fallback local |
| Catálogo editorial | Preparada e fechada | `EDITORIAL_CONTENT_READY` + `STAFF_ACCESS_READY`; importador valida rotas e âncoras internas | CRUD administrativo, publicação, retirada e auditoria |
| Exposição fotográfica | Ativa localmente | Conteúdo público independente das integrações privadas | `/expo` e assets na mesma origem |

A AI nunca substitui a meditação oficial. Falha de fornecedor, autenticação, quota ou validação devolve conteúdo local sem bloquear a experiência.

## Ajuda e comunidade

| Capacidade | Estado | Porta ou limite | Evidência |
| --- | --- | --- | --- |
| Diretório verificado | Preparada e fechada | `HELP_DIRECTORY_READY` + equipa autorizada; só publica recursos verificados e dentro do prazo | endpoints públicos/administrativos e importador de rascunhos |
| Sala Anónima local | Ativa localmente | Diário guardado apenas no dispositivo; não simula conversa real | interface pública com modo local explícito |
| Comunidade moderada | Preparada e fechada | `COMMUNITY_READY`, conta e `STAFF_ACCESS_READY`; saída pública revalidada no servidor e navegador | envio pendente, pseudónimo do servidor, denúncia e moderação |
| Botão SOS | Ativa localmente | Encaminha para apoio humano; não presta atendimento clínico | modal SOS e secção Ajuda |
| Moderação operacional | Depende da equipa | Dois moderadores, escalas, retenção, regras e protocolo de crise | pendente na checklist de ativação |

## Administração e segurança

| Capacidade | Estado | Proteção | Evidência |
| --- | --- | --- | --- |
| Painel da equipa | Ativa em produção | `/admin`, OTP sem criação automática e `STAFF_ACCESS_READY` | conta `admin` real; acesso permitido, suspensão, recusa e restauração validados; respostas `no-store` |
| Papéis mínimos | Admin ativo; editores de conteúdo e ajuda validados; moderação preparada | `admin`, `moderator`, `help_editor`, `content_editor` | `staff_roles`; isolamento real dos editores, validação por endpoint e privilégios SQL explícitos para `service_role` |
| Auditoria editorial | Preparada e fechada | eventos mínimos por trigger; sem texto privado | `staff_audit_events` |
| Limites comunitários e AI | Preparada e fechada | reclamação atómica diária no servidor | RPCs de quota no Supabase |
| Política de privacidade | Depende da equipa | versão preliminar pública; revisão jurídica pendente | `/privacidade` |
| Teste de acessibilidade em dispositivo | Depende da equipa | foco e teclado automatizados; VoiceOver/TalkBack pendentes | checklist e testes web |

## Funcionalidades secundárias

| Capacidade | Estado | Motivo | Decisão necessária |
| --- | --- | --- | --- |
| Loja | Não iniciada | Não existe operação completa e segura | entidade, catálogo, stock, preços, pagamentos, entregas, devoluções e recibos |
| Doação | Não iniciada | Não existe modelo financeiro e de transparência aprovado | entidade beneficiária, método, prestação de contas e conformidade |

Loja e doação não devem aparecer como botões inativos. Só entram na interface quando o respetivo fluxo puder ser concluído de ponta a ponta.

## Auditoria antes de ativar

1. Confirmar variáveis e flags sem revelar valores:

   ```bash
   PYTHONPATH=src python scripts/check_readiness.py
   ```

2. Confirmar tabelas e RPCs por leitura do OpenAPI do Supabase:

   ```bash
   PYTHONPATH=src python scripts/check_supabase_schema.py
   ```

3. Executar testes automatizados:

   ```bash
   PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
   node --test tests/*.mjs
   ```

4. Concluir todos os itens humanos e de dispositivo em `docs/ACTIVATION_CHECKLIST.md`.

   As decisões de responsabilidade, moderação, retenção, incidentes e consentimento devem ser registadas em `docs/OPERATIONS_DECISIONS.md` sem incluir segredos ou dados pessoais.

5. Ativar primeiro em Preview. Produção só recebe a mesma configuração depois de testes reais e aprovação da equipa.
