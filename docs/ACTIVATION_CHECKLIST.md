# Checklist de ativacao

Esta checklist separa o que ja esta implementado do que precisa de configuracao, validacao humana ou operacao permanente. Ativar primeiro no ambiente `dev`; so promover para `production` depois de todos os testes da respetiva fase.

## 1. Base tecnica

- [x] Cinco areas principais com navegacao inferior responsiva.
- [x] Navegação inferior verificada em viewport móvel e desktop, sem corte lateral e com espaço reservado para não tapar o conteúdo final.
- [x] Meditacao, Jornada, Viver Saudavel, Ajuda e Sobre funcionais em modo local.
- [x] Sala Anónima local identificada como diário privado, sem envio remoto, com eliminação individual das partilhas.
- [x] Dias limpos, sequência atual, melhor sequência e arquivo usam aritmética UTC para datas civis, verificada em mudanças de mês, ano e 29 de fevereiro.
- [x] Uma PWA deixada aberta deteta a mudança de dia ao regressar ao ecrã ou durante a utilização e carrega a nova meditação, inclusive pelo catálogo offline.
- [x] PWA instalavel com ícones 192/512, base diaria offline e fallbacks separados para app, privacidade e exposicao.
- [x] Atualizações de assets servidos da cache permanecem ligadas ao ciclo de vida do service worker; navegações só concluem depois de atualizar o fallback correspondente.
- [x] Instalação orientada no contexto certo, com instruções específicas para iPhone/iPad, Android e desktop quando o navegador não oferece o prompt automático.
- [x] O manifesto não força orientação e não anuncia como maskable um ícone sem área segura dedicada.
- [x] Apoio diário local preserva dia e estado offline; atualizações da PWA exigem ação explícita.
- [x] Navegação offline validada em Chromium local para a aplicação, `/expo` e `/privacidade`, com a meditação e as cinco áreas principais disponíveis.
- [x] Arquivo anual permite reler meditacoes por data sem alterar leitura, check-in ou sequencia do dia atual.
- [x] A partilha da meditação abre uma prévia e permite escolher a folha nativa ou copiar texto, sem anexar URL que possa duplicar a mensagem.
- [x] A imagem 9:16 inclui a fonte e a autorização de reprodução; cancelar a folha nativa não é apresentado como erro.
- [x] Importação da planilha sincroniza a base canónica e a cópia pública; os testes recusam divergências nas meditações e no catálogo de apoio.
- [x] Players de video e podcast usam incorporacao YouTube com privacidade reforcada, sem referencia da pagina e com CSP restrita.
- [x] Servidor local real e interface verificados sem segredos: conta, AI remota, comunidade pública, diretório gerido e push permanecem desativados por defeito.
- [x] O cliente recusa uma configuração de conta cujo destino Supabase não seja uma origem HTTPS sem credenciais, caminho, query ou fragmento.
- [x] Conta, equipa, AI, push, comunidade, Ajuda e conteúdo editorial aplicam a mesma validação de origem no servidor antes de usarem chaves privadas.
- [x] Subscrições push são validadas no cliente, na base de dados e antes da entrega; endpoints inseguros ou chaves malformadas são desativados sem contacto de rede.
- [x] Exportacao local versionada e importacao da Jornada validada, limitada a 1 MB e confirmada antes da substituicao.
- [x] Falhas, bloqueio ou quota do armazenamento local não interrompem a aplicação e são anunciados num aviso persistente antes de novos registos se perderem ao fechar.
- [x] Importar uma cópia nunca a envia automaticamente para a conta; a sincronização ativa é pausada até uma nova escolha explícita.
- [x] Sincronizacao preparada para recusar versoes futuras, pausar quando outra copia remota for mais recente e excluir dados exclusivos do dispositivo.
- [x] Cursor remoto por conta impede que sincronização automática ressuscite uma Jornada eliminada ou sobrescreva uma versão alterada noutro dispositivo.
- [x] Testes automaticos no GitHub Actions para `dev`, `production` e pull requests.
- [x] Referências locais, rotas limpas, âncoras entre páginas, assets CSS e isolamento de links externos são validados automaticamente.
- [x] Navegação principal suporta atalho para o conteúdo, setas/Home/End, ativação explícita e anúncio da área aberta para tecnologias de apoio.
- [x] Breakpoints visuais e interativos do menu da exposição estão alinhados; links fora do ecrã ficam inertes e movimento reduzido é respeitado.
- [ ] Confirmar instalacao e atualizacao da PWA em Android Chrome e iPhone Safari seguindo `docs/PWA_DEVICE_TEST.md`.
- [ ] Confirmar os contactos e horarios comunitarios diretamente com cada entidade.

## 2. Supabase no ambiente dev

- [x] Criar o projeto Supabase na regiao escolhida pela equipa (`Só Por Hoje Dev`, West Europe/London).
- [x] Rever e executar `supabase/schema.sql`; 11 tabelas confirmadas com RLS ativo e Security Advisor sem erros ou avisos.
- [x] Verificar o esquema real no catálogo Supabase: 11 tabelas com RLS e todas as tabelas e RPCs esperadas presentes, sem objetos em falta.
- [x] Integrar Cloudflare Turnstile no pedido OTP público e da equipa; token de uso único e bloqueio seguro validados localmente com a chave oficial de teste.
- [x] Configurar SMTP próprio no Supabase com o remetente aprovado `Só Por Hoje Viver Saudável <viversaudavel@soporhoje.cv>` e aplicar `docs/OTP_EMAIL_TEMPLATE.md` apenas com `{{ .Token }}`, sem link mágico.
- [x] Validar no Gmail a entrega real do código OTP com assunto personalizado, corpo token-only e logótipo Viver Saudável no rodapé.
- [x] Conceder às contas autenticadas os privilégios mínimos das tabelas pessoais e validar uma gravação real da Jornada com RLS ativa.
- [ ] Validar o limite por utilizador e a apresentação do código OTP em Outlook e num endereço fora da equipa Supabase.
- [x] Criar o widget Turnstile para os domínios autorizados, guardar a secret key em `Authentication > Attack Protection` no Supabase e `TURNSTILE_SITE_KEY` na Vercel.
- [x] Isolar o teste de conta: Preview usa as chaves oficiais de teste Turnstile e `ACCOUNT_READY=true`; Production conserva a chave real e `ACCOUNT_READY=false`.
- [ ] Antes de ativar contas em produção, restaurar a secret key real no Supabase, validar o hostname definitivo e testar novamente com a site key real.
- [x] Configurar Site URL `https://soporhoje.cv` e Redirect URLs para produção, Vercel e preview local autorizado.
- [x] Guardar na Vercel Production, Preview e Development: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` e `SUPABASE_SERVICE_ROLE_KEY`.
- [x] Guardar `TURNSTILE_SITE_KEY` nos três ambientes da Vercel depois de criar o widget definitivo.
- [x] `ACCOUNT_READY=false` mantém conta, sincronização, AI, push e comunidade ocultos enquanto o Supabase está em configuração.
- [ ] Mudar `ACCOUNT_READY=true` apenas depois de validar RLS, Email OTP, SMTP, CAPTCHA e os fluxos com duas contas.
- [ ] Gerar e guardar `ADMIN_API_SECRET` para os endpoints tecnicos; nao o reutilizar noutros servicos.
- [x] Papéis individuais `admin`, `moderator` e `help_editor` preparados no esquema e validados pelo servidor sem exposição ao browser.
- [ ] Atribuir papéis mínimos a contas reais da equipa e ativar `STAFF_ACCESS_READY=true` apenas depois de testar suspensão e acesso negado.
- [x] Confirmar com as duas contas reais que a RLS da Jornada devolve apenas a linha da identidade autenticada e nenhuma linha da outra conta.
- [x] Testar escolha entre copia local e copia da conta nos dois sentidos.
- [ ] Testar eliminacao da Jornada, eliminacao da conta e limpeza local com duas contas reais.

## 3. Notificacoes em segundo plano

- [ ] Gerar um par VAPID fora do repositorio.
- [ ] Guardar na Vercel Preview: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` e `PUSH_CRON_SECRET`.
- [ ] Manter `PUSH_DELIVERY_READY=false` durante os primeiros testes.
- [x] `PUSH_DELIVERY_READY=false` bloqueia o emissor no servidor, mesmo com Supabase, VAPID e segredo do cron configurados.
- [x] O browser só recebe a funcionalidade push quando todas as credenciais de subscrição e entrega estão presentes no servidor.
- [x] O estado mostrado é reconciliado com a permissão e a subscrição reais do navegador; uma subscrição órfã é removida sem reagir destrutivamente a uma falha transitória de configuração.
- [x] Textos de privacidade distinguem a cópia da Jornada do registo técnico separado usado apenas quando o push real é ativado.
- [x] A reconciliação push exige também a preferência local ativa e tenta retirar o endpoint remoto antes de remover uma subscrição que deixou de ser válida.
- [ ] Guardar o endpoint e o segredo do cron no Supabase Vault.
- [ ] Agendar `POST /api/v1/internal/push/deliver` a cada minuto com `Authorization: Bearer $PUSH_CRON_SECRET`.
- [ ] Testar subscricao, hora/fuso, entrega com app fechada, cancelamento e endpoint expirado em dois dispositivos.
- [x] O servidor e o service worker limitam o ecrã bloqueado a uma mensagem genérica e ignoram texto recebido no payload push.
- [x] Uma reserva atómica por conta e dia impede notificações duplicadas em ciclos concorrentes e permite repetir falhas transitórias.
- [x] Resposta de subscrições malformada é tratada como falha transitória e nunca desativa silenciosamente a preferência da pessoa.
- [ ] Confirmar que o ecrã bloqueado mostra apenas a mensagem generica.
- [ ] Mudar `PUSH_DELIVERY_READY=true` apenas depois do teste integral.

## 4. Apoio diário com AI

- [x] Manter o catálogo local disponível para todas as pessoas e como fallback automático.
- [x] Sem AI ativa e sessão válida, atividade, frase e desafio são escolhidos inteiramente no navegador, sem enviar check-in ou métricas ao servidor.
- [x] Exigir conta validada e reclamar a quota diária de forma atómica antes de chamar a OpenAI.
- [ ] Guardar na Vercel Preview: `OPENAI_API_KEY`, `OPENAI_MODEL` e `AI_DAILY_LIMIT`.
- [ ] Manter `AI_DELIVERY_READY=false` durante a configuração e os primeiros testes.
- [ ] Confirmar no Supabase que `ai_daily_usage` guarda apenas conta, data, contador e atualização.
- [x] Testes automatizados confirmam que utilizador sem conta, sessão inválida, limite atingido e falha da OpenAI recebem sempre o catálogo local.
- [x] O servidor substitui contexto enviado pelo browser pela meditação canónica e rejeita respostas remotas excessivas ou inseguras.
- [x] O browser envia ao endpoint de AI apenas a data da meditação e o contexto pessoal mínimo; título, corpo e reflexão são resolvidos no servidor.
- [ ] Rever custos e definir o limite diário inicial; recomendado: `3`.
- [ ] Mudar `AI_DELIVERY_READY=true` apenas em Preview e monitorizar custo, latência e falhas antes de produção.

## 5. Conteudo e seguranca

- [x] Modelo de decisões operacionais preparado em `docs/OPERATIONS_DECISIONS.md`, sem assumir responsáveis, prazos ou aprovação.
- [ ] Rever atividade, frase e desafio com pessoas com experiencia clinica e comunitaria.
- [ ] Aprovar a politica de privacidade com apoio juridico adequado a Cabo Verde.
- [ ] Definir retencao, auditoria e resposta a incidentes.
- [x] Confirmar no codigo que nao sao escritos em logs check-ins, gratidoes, partilhas ou dados privados da Jornada.
- [ ] Confirmar na Vercel e no Supabase que captura de pedidos e logs tecnicos nao guardam corpos privados.
- [x] Garantir foco visível, ciclo de teclado nos modais, estados anunciados e movimento reduzido.
- [ ] Fazer um teste manual com VoiceOver e TalkBack em dispositivos reais.

### Diretório de ajuda verificado

- [x] Backend e interface preparados para mostrar apenas recursos verificados e dentro do prazo de revisão.
- [x] Catálogo inicial de rascunhos e importador idempotente preparados sem exigir a ativação pública do diretório.
- [x] Todos os 17 rascunhos têm representação no fallback local; indisponibilidade do serviço gerido preserva essa lista e anuncia o estado.
- [x] Recursos novos ou alterados regressam automaticamente a rascunho.
- [x] A verificação recusa reuniões sem horário/contacto, emergências sem telefone e ligações que não usem HTTPS.
- [x] Acesso direto pelo browser removido; gestão exige endpoint administrativo protegido.
- [x] O browser revalida e deduplica a resposta pública, rejeitando recursos expirados, malformados ou sem contacto obrigatório antes de substituir o fallback local.
- [x] Linha SOS Álcool, contactos gerais da CCAD e telefones oficiais do Centro de Saúde de Tira Chapéu revistos em fontes públicas atuais; horários comunitários continuam claramente assinalados para confirmação.
- [ ] Importar todos os contactos como rascunho, sem os tornar públicos.
- [ ] Confirmar cada contacto e horário diretamente com a entidade responsável.
- [ ] Guardar a fonte e definir o prazo de revisão de cada recurso.
- [ ] Testar expiração, retirada e indisponibilidade do diretório em Preview.
- [ ] Mudar `HELP_DIRECTORY_READY=true` apenas depois de todos os recursos visíveis estarem confirmados.

## 6. Funcionalidades que ficam fechadas

### Sala Anonima publica

Nao ativar antes de existirem moderadores identificados, horario e tempo de resposta, regras de publicacao, denuncia, retencao e protocolo de crise. A versao atual permanece um diario local e diz isso claramente.

- [x] Backend preparado com partilha pendente, pseudónimo gerado no servidor, listagem pública mínima, denúncia e moderação protegida.
- [x] Cliente público preparado para ler partilhas aprovadas e, com conta validada, enviar para moderação e denunciar; o modo local permanece quando a flag está fechada.
- [x] `COMMUNITY_READY=false` mantém todos os endpoints comunitários indisponíveis por defeito.
- [x] Limite diário atómico protege a fila de moderação; valor inicial recomendado: `3`.
- [x] Saída pública revalidada e transições de moderação limitadas para impedir exposição de registos malformados ou republicação acidental.
- [x] O navegador volta a validar e deduplicar a lista pública e bloqueia denúncias repetidas durante a mesma sessão.
- [x] Telefones, emails e ligações são assinalados para revisão e bloqueados antes da publicação; a decisão continua humana.
- [ ] Nomear pelo menos dois moderadores e definir escalas, permissões e substituição.
- [ ] Preencher e aprovar as secções de comunidade, risco e retenção em `docs/OPERATIONS_DECISIONS.md`.
- [ ] Aprovar regras de publicação, motivos de denúncia, retenção e auditoria.
- [ ] Aprovar e ensaiar o protocolo para conteúdo de risco antes de receber uma única partilha pública.
- [x] Preparar a interface administrativa separada em `/admin`, com acesso por código e permissões individuais para moderação e diretório.
- [x] Painel administrativo inclui navegação por teclado, atalho para conteúdo, nomes acessíveis em campos dinâmicos e bloqueio de mutações administrativas concorrentes.
- [x] Limitar o resumo operacional de envios ao papel `admin` e omitir destinos, conteúdo, hashes e erros brutos da resposta ao browser.
- [x] Registar alterações editoriais do painel por trigger atómico, sem copiar conteúdo privado para `staff_audit_events`.
- [x] Preparar catálogo editorial de Viver Saudável com rascunho, publicação, retirada, papel `content_editor` e auditoria privada.
- [x] Preparar catálogo inicial validado e importador idempotente que mantém todos os conteúdos em rascunho.
- [x] Importador editorial recusa rotas ou âncoras internas inexistentes antes de criar rascunhos.
- [x] Revalidar no navegador as ligações editoriais e carregar os players da aplicação principal apenas depois da escolha da pessoa.
- [x] Revalidar e deduplicar no navegador todo o contrato editorial público, limitando textos e mantendo imagens remotas bloqueadas.
- [x] Preservar o diretório local de Ajuda perante falha ou resposta vazia e revalidar no navegador telefone, email e ligações HTTPS.
- [ ] Importar o catálogo editorial inicial em Preview e rever cada título, resumo, ligação, imagem, autoria e consentimento.
- [ ] Testar criação, edição, publicação e retirada de conteúdos editoriais com uma conta real em Preview.
- [ ] Ativar `EDITORIAL_CONTENT_READY=true` apenas depois de rever todas as ligações e confirmar autoria/consentimento dos conteúdos publicados.
- [ ] Testar `/admin` com contas reais de cada papel antes de ativar `STAFF_ACCESS_READY=true`.
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
