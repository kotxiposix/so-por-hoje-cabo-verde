# Checklist de ativacao

Esta checklist separa o que ja esta implementado do que precisa de configuracao, validacao humana ou operacao permanente. Ativar primeiro no ambiente `dev`; so promover para `production` depois de todos os testes da respetiva fase.

## 1. Base tecnica

- [x] Cinco areas principais com navegacao inferior responsiva.
- [x] Navegação inferior verificada em viewport móvel e desktop, sem corte lateral e com espaço reservado para não tapar o conteúdo final.
- [x] Meditacao, Jornada, Viver Saudavel, Ajuda e Sobre funcionais em modo local.
- [x] PWA instalavel, base diaria offline e fallbacks separados para app, privacidade e exposicao.
- [x] Apoio diário local preserva dia e estado offline; atualizações da PWA exigem ação explícita.
- [x] Navegação offline validada em Chromium local para a aplicação, `/expo` e `/privacidade`, com a meditação e as cinco áreas principais disponíveis.
- [x] Arquivo anual permite reler meditacoes por data sem alterar leitura, check-in ou sequencia do dia atual.
- [x] Importação da planilha sincroniza a base canónica e a cópia pública; os testes recusam divergências nas meditações e no catálogo de apoio.
- [x] Players de video e podcast usam incorporacao YouTube com privacidade reforcada, sem referencia da pagina e com CSP restrita.
- [x] Exportacao local versionada e importacao da Jornada validada, limitada a 1 MB e confirmada antes da substituicao.
- [x] Sincronizacao preparada para recusar versoes futuras, pausar quando outra copia remota for mais recente e excluir dados exclusivos do dispositivo.
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
- [ ] Testar eliminacao da Jornada, eliminacao da conta e limpeza local com duas contas reais.

## 3. Notificacoes em segundo plano

- [ ] Gerar um par VAPID fora do repositorio.
- [ ] Guardar na Vercel Preview: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` e `PUSH_CRON_SECRET`.
- [ ] Manter `PUSH_DELIVERY_READY=false` durante os primeiros testes.
- [ ] Guardar o endpoint e o segredo do cron no Supabase Vault.
- [ ] Agendar `POST /api/v1/internal/push/deliver` a cada minuto com `Authorization: Bearer $PUSH_CRON_SECRET`.
- [ ] Testar subscricao, hora/fuso, entrega com app fechada, cancelamento e endpoint expirado em dois dispositivos.
- [ ] Confirmar que o ecrã bloqueado mostra apenas a mensagem generica.
- [ ] Mudar `PUSH_DELIVERY_READY=true` apenas depois do teste integral.

## 4. Apoio diário com AI

- [x] Manter o catálogo local disponível para todas as pessoas e como fallback automático.
- [x] Exigir conta validada e reclamar a quota diária de forma atómica antes de chamar a OpenAI.
- [ ] Guardar na Vercel Preview: `OPENAI_API_KEY`, `OPENAI_MODEL` e `AI_DAILY_LIMIT`.
- [ ] Manter `AI_DELIVERY_READY=false` durante a configuração e os primeiros testes.
- [ ] Confirmar no Supabase que `ai_daily_usage` guarda apenas conta, data, contador e atualização.
- [ ] Testar utilizador sem conta, sessão inválida, limite atingido e falha da OpenAI; todos devem receber o catálogo local.
- [ ] Rever custos e definir o limite diário inicial; recomendado: `3`.
- [ ] Mudar `AI_DELIVERY_READY=true` apenas em Preview e monitorizar custo, latência e falhas antes de produção.

## 5. Conteudo e seguranca

- [ ] Rever atividade, frase e desafio com pessoas com experiencia clinica e comunitaria.
- [ ] Aprovar a politica de privacidade com apoio juridico adequado a Cabo Verde.
- [ ] Definir retencao, auditoria e resposta a incidentes.
- [x] Confirmar no codigo que nao sao escritos em logs check-ins, gratidoes, partilhas ou dados privados da Jornada.
- [ ] Confirmar na Vercel e no Supabase que captura de pedidos e logs tecnicos nao guardam corpos privados.
- [x] Garantir foco visível, ciclo de teclado nos modais, estados anunciados e movimento reduzido.
- [ ] Fazer um teste manual com VoiceOver e TalkBack em dispositivos reais.

### Diretório de ajuda verificado

- [x] Backend e interface preparados para mostrar apenas recursos verificados e dentro do prazo de revisão.
- [x] Recursos novos ou alterados regressam automaticamente a rascunho.
- [x] Acesso direto pelo browser removido; gestão exige endpoint administrativo protegido.
- [ ] Importar todos os contactos como rascunho, sem os tornar públicos.
- [ ] Confirmar cada contacto e horário diretamente com a entidade responsável.
- [ ] Guardar a fonte e definir o prazo de revisão de cada recurso.
- [ ] Testar expiração, retirada e indisponibilidade do diretório em Preview.
- [ ] Mudar `HELP_DIRECTORY_READY=true` apenas depois de todos os recursos visíveis estarem confirmados.

## 6. Funcionalidades que ficam fechadas

### Sala Anonima publica

Nao ativar antes de existirem moderadores identificados, horario e tempo de resposta, regras de publicacao, denuncia, retencao e protocolo de crise. A versao atual permanece um diario local e diz isso claramente.

- [x] Backend preparado com partilha pendente, pseudónimo gerado no servidor, listagem pública mínima, denúncia e moderação protegida.
- [x] `COMMUNITY_READY=false` mantém todos os endpoints comunitários indisponíveis por defeito.
- [x] Limite diário atómico protege a fila de moderação; valor inicial recomendado: `3`.
- [ ] Nomear pelo menos dois moderadores e definir escalas, permissões e substituição.
- [ ] Aprovar regras de publicação, motivos de denúncia, retenção e auditoria.
- [ ] Aprovar e ensaiar o protocolo para conteúdo de risco antes de receber uma única partilha pública.
- [ ] Construir e testar a área administrativa com contas individuais; não usar um segredo partilhado como solução final.
- [ ] Testar publicação, rejeição, ocultação, denúncia duplicada e eliminação de conta em Preview.
- [ ] Só depois destes passos ativar `COMMUNITY_READY=true` em Preview.

### Loja e doacao

Nao ativar antes de definir entidade responsavel, catalogo, stock, precos, pagamentos, entregas, devolucoes, recibos e transparencia sobre o destino do apoio.

## 7. Promocao para producao

- [ ] Repetir no projeto e variaveis de Production tudo o que foi validado em Preview.
- [ ] Confirmar `production` como Production Branch na Vercel.
- [ ] Executar a suite automatica e o roteiro manual em telemovel e desktop.
- [ ] Verificar `soporhoje.cv`, `/expo`, `/privacidade` e os endpoints publicos.
- [ ] Confirmar que endpoints internos recusam pedidos sem credenciais.
- [ ] Confirmar no deploy os cabecalhos CSP, HSTS, `no-store` da API e revalidacao de `sw.js`.
- [ ] Preparar responsavel e contacto para incidentes antes de anunciar conta ou push.

## Dados que a equipa precisa fornecer

1. Projeto Supabase e decisao de regiao.
2. Servico SMTP/remetente e CAPTCHA.
3. Email oficial para `VAPID_SUBJECT`.
4. Responsaveis por privacidade, suporte e moderacao.
5. Confirmacao operacional para loja/doacao, caso avancem.

Segredos devem ser introduzidos diretamente nos painéis Supabase e Vercel. Nunca devem ser enviados em mensagens, colocados em capturas de ecrã ou guardados no Git.
