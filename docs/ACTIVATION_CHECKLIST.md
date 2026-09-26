# Checklist de ativacao

Esta checklist separa o que ja esta implementado do que precisa de configuracao, validacao humana ou operacao permanente. Ativar primeiro no ambiente `dev`; so promover para `production` depois de todos os testes da respetiva fase.

## 1. Base tecnica

- [x] Cinco areas principais com navegacao inferior responsiva.
- [x] Meditacao, Jornada, Viver Saudavel, Ajuda e Sobre funcionais em modo local.
- [x] PWA instalavel, base diaria offline e fallbacks separados para app, privacidade e exposicao.
- [x] Testes automaticos no GitHub Actions para `dev`, `production` e pull requests.
- [ ] Confirmar instalacao e atualizacao da PWA em Android Chrome e iPhone Safari.
- [ ] Confirmar os contactos e horarios comunitarios diretamente com cada entidade.

## 2. Supabase no ambiente dev

- [ ] Criar o projeto Supabase na regiao escolhida pela equipa.
- [ ] Rever e executar `supabase/schema.sql`.
- [ ] Configurar Email OTP, SMTP proprio, remetente e CAPTCHA.
- [ ] Configurar Site URL e Redirect URLs apenas para os dominios `dev` autorizados.
- [ ] Guardar na Vercel Preview: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` e `SUPABASE_SERVICE_ROLE_KEY`.
- [ ] Gerar e guardar `ADMIN_API_SECRET` para os endpoints tecnicos; nao o reutilizar noutros servicos.
- [ ] Entrar com duas contas diferentes e confirmar que a RLS impede acesso cruzado.
- [ ] Testar escolha entre copia local e copia da conta nos dois sentidos.
- [ ] Testar exportacao, eliminacao da Jornada, eliminacao da conta e limpeza local.

## 3. Notificacoes em segundo plano

- [ ] Gerar um par VAPID fora do repositorio.
- [ ] Guardar na Vercel Preview: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` e `PUSH_CRON_SECRET`.
- [ ] Manter `PUSH_DELIVERY_READY=false` durante os primeiros testes.
- [ ] Guardar o endpoint e o segredo do cron no Supabase Vault.
- [ ] Agendar `POST /api/v1/internal/push/deliver` a cada minuto com `Authorization: Bearer $PUSH_CRON_SECRET`.
- [ ] Testar subscricao, hora/fuso, entrega com app fechada, cancelamento e endpoint expirado em dois dispositivos.
- [ ] Confirmar que o ecrã bloqueado mostra apenas a mensagem generica.
- [ ] Mudar `PUSH_DELIVERY_READY=true` apenas depois do teste integral.

## 4. Conteudo e seguranca

- [ ] Rever atividade, frase e desafio com pessoas com experiencia clinica e comunitaria.
- [ ] Aprovar a politica de privacidade com apoio juridico adequado a Cabo Verde.
- [ ] Definir retencao, auditoria e resposta a incidentes.
- [ ] Confirmar que logs tecnicos nunca incluem meditacao privada, check-ins, gratidoes ou partilhas.
- [ ] Fazer um teste de acessibilidade com leitor de ecrã e navegacao por teclado.

## 5. Funcionalidades que ficam fechadas

### Sala Anonima publica

Nao ativar antes de existirem moderadores identificados, horario e tempo de resposta, regras de publicacao, denuncia, retencao e protocolo de crise. A versao atual permanece um diario local e diz isso claramente.

### Loja e doacao

Nao ativar antes de definir entidade responsavel, catalogo, stock, precos, pagamentos, entregas, devolucoes, recibos e transparencia sobre o destino do apoio.

## 6. Promocao para producao

- [ ] Repetir no projeto e variaveis de Production tudo o que foi validado em Preview.
- [ ] Confirmar `production` como Production Branch na Vercel.
- [ ] Executar a suite automatica e o roteiro manual em telemovel e desktop.
- [ ] Verificar `soporhoje.cv`, `/expo`, `/privacidade` e os endpoints publicos.
- [ ] Confirmar que endpoints internos recusam pedidos sem credenciais.
- [ ] Preparar responsavel e contacto para incidentes antes de anunciar conta ou push.

## Dados que a equipa precisa fornecer

1. Projeto Supabase e decisao de regiao.
2. Servico SMTP/remetente e CAPTCHA.
3. Email oficial para `VAPID_SUBJECT`.
4. Responsaveis por privacidade, suporte e moderacao.
5. Confirmacao operacional para loja/doacao, caso avancem.

Segredos devem ser introduzidos diretamente nos painéis Supabase e Vercel. Nunca devem ser enviados em mensagens, colocados em capturas de ecrã ou guardados no Git.
