# Dossie de Documentacao da Plataforma

## So Por Hoje Cabo Verde

Este documento serve para alinhar equipa, parceiros e decisores sobre a evolucao da plataforma So Por Hoje Cabo Verde. O objetivo e juntar num unico sitio a visao funcional, as decisoes tecnicas, as sugestoes de experiencia de utilizador e os pontos que precisam de validacao antes de crescer.

**Ultima atualizacao:** 29 de setembro de 2026.

Este dossie apresenta a visao do produto. O estado verificavel de cada capacidade esta em `IMPLEMENTATION_MATRIX.md`, os passos de ativacao estao em `ACTIVATION_CHECKLIST.md` e as responsabilidades ainda por decidir devem ser registadas em `OPERATIONS_DECISIONS.md`. Nenhuma descricao neste documento substitui essas portas de seguranca.

## 1. Visao

A plataforma nasce para apoiar pessoas em recuperacao, disponibilizando diariamente a meditacao "So Por Hoje" e criando uma experiencia complementar de acompanhamento, inspiracao, ajuda e comunidade.

O foco nao e marketing nem entretenimento. O foco e consistencia, serenidade, acesso simples a recursos de recuperacao e encaminhamento para ajuda real quando necessario.

## 2. Publico principal

- Pessoas em recuperacao de dependencia.
- Pessoas que querem acompanhar dias limpos/sobrios.
- Familiares ou amigos que procuram orientacao inicial.
- Membros e servidores da comunidade.
- Equipas que organizam reunioes, eventos, exposicoes, podcast e conteudos de recuperacao.

## 3. Principios de produto

- Simples antes de complexo.
- Privacidade por defeito.
- Conteudo oficial preservado sem alteracoes.
- A plataforma nao substitui profissionais de saude, terapeutas, reunioes, sponsor ou servicos de emergencia.
- Tudo deve funcionar bem no telemovel.
- Cada funcionalidade deve ajudar a pessoa a dar o proximo passo, nao criar pressao ou culpa.

## 4. Estrutura atual

### Aplicacao principal

URL principal: `/`

Secoes atuais:

- Meditacao
- Jornada
- Viver Saudavel
- Ajuda
- Sobre

Funcoes principais:

- Mostrar a meditacao diaria.
- Marcar meditacao como lida.
- Abrir Oracao da Serenidade.
- Partilhar texto no formato do grupo.
- Gerar e partilhar uma imagem vertical para stories/status.
- Ativar notificacao.
- Ver atividade do dia, frase do dia e desafio mental.
- Guardar gratidao e plano pessoal apenas no dispositivo.
- Acompanhar dias limpos/sobrios.
- Fazer check-in pessoal.
- Consultar o arquivo anual sem alterar o progresso do dia.
- Exportar e importar uma copia versionada da Jornada.
- Ver recursos de ajuda.

### Pagina da exposicao

URL: `/expo`

Secoes atuais:

- Inicio
- Bem-vindos
- Catalogo
- Experiencia
- Exposicoes
- Bio
- Contacto

Funcoes principais:

- Apresentar a exposicao fotografica "So Por Hoje".
- Mostrar colecoes fotograficas.
- Integrar videos, documentario e podcast.
- Apresentar biografia e contactos do autor.
- Servir como pagina viva da exposicao ao longo do tempo.

## 5. Fonte unica da verdade

As meditacoes devem continuar numa unica base de dados reutilizavel.

Regra principal:

- A chave da meditacao e `MM-DD`.
- O ano nao pertence ao registo da meditacao.
- O ano so aparece quando o sistema gera a mensagem do dia.

Esta decisao evita duplicacao anual e permite usar o mesmo conteudo em:

Os canais abaixo representam destinos possiveis da mesma base; apenas a web app, a API e os fluxos descritos como ativos na matriz estao implementados atualmente.

- Web app.
- Messenger.
- WhatsApp.
- Telegram.
- Email.
- API publica.
- App mobile.
- Painel administrativo.

## 6. Meditacao diaria

### Objetivo

Entregar a meditacao do dia com clareza, respeito ao texto oficial e acoes simples.

### Estado atual

- A meditacao carrega de `public/data/meditations.json`.
- Existe fallback local.
- O conteudo mostra fonte oficial e aviso de permissao.
- A leitura pode ser marcada como concluida.
- O arquivo anual permite consultar qualquer meditacao por data, inclusive offline, sem alterar o estado do dia atual.

### Sugestoes

- Manter o texto da meditacao intacto.
- Separar claramente conteudo oficial de reflexoes, atividades e desafios criados pela plataforma.
- Criar estado offline para quando a internet falhar.
- Adicionar audio da meditacao quando houver permissao e producao adequada.

### Decisoes a validar

- O texto oficial pode ser exibido integralmente na web publica?
- Quais limites de uso definidos por Narcotics Anonymous World Services?
- Como apresentar melhor direitos, fonte e permissao sem quebrar a experiencia?

## 7. Jornada

### Objetivo

Acompanhar recuperacao pessoal sem julgamento, com foco em dias limpos, consistencia e pedido de ajuda.

### Estado atual

- Utilizador pode definir data de sobriedade.
- Sistema calcula dias limpos.
- Mostra sequencia de meditacoes lidas.
- O historico pessoal permite reabrir a meditacao correspondente sem alterar o estado do dia atual.
- Check-in permite estados como firme, preciso de serenidade, estou em risco e voltei a consumir.

### Sugestoes

- Trocar linguagem de culpa por linguagem de cuidado.
- Em vez de "falhei", usar "recomecar hoje".
- Mostrar progresso como caminhada, nao como competicao.
- Premiacoes devem celebrar consistencia e coragem, nao perfeicao.

### Sistema de recompensa sugerido

- 1 leitura: "So por hoje"
- 7 leituras seguidas: "Uma semana presente"
- 30 leituras no mes: "Rotina de cuidado"
- 90 dias limpos: "Compromisso vivo"
- 6 meses: "Caminhada firme"
- 1 ano: "Um dia de cada vez"

Recompensas recomendadas:

- Selos visuais discretos.
- Mensagens motivacionais.
- Marcos pessoais.
- Sem rankings publicos.
- Sem comparacao entre pessoas.

### Decisoes tomadas e validacoes pendentes

- O modo local e anonimo e o comportamento por defeito.
- A conta opcional por codigo de email e a sincronizacao seletiva estao ativas em producao com `ACCOUNT_READY=true`, depois da validacao de Supabase, SMTP, CAPTCHA, RLS e fluxos com duas contas.
- `ACCOUNT_READY=false` continua a ser a porta de reversao segura: oculta conta e sincronizacao sem afetar a Jornada local.
- Partilhas da Sala Anonima local, instalacao e permissoes do dispositivo nao entram na sincronizacao da Jornada.
- Exportacao, eliminacao local, eliminacao da copia remota e eliminacao da conta estao preparadas.
- A politica de privacidade continua preliminar ate revisao juridica e validacao operacional.

## 8. Viver Saudavel

### Objetivo

Reunir conteudos de inspiracao, exposicao, podcast, testemunhos e partilhas que ajudem a pessoa a continuar.

### Estado atual

- Existe secao da exposicao dentro da app.
- A pagina `/expo` apresenta catalogo, videos, podcast, exposicoes, bio e contacto.
- Na aplicação principal, podcast e vídeos só contactam o YouTube depois da escolha explícita da pessoa; a referência técnica limita-se à origem do site.
- Existe uma Sala Anonima local, apresentada explicitamente como diario privado no dispositivo.
- O catálogo editorial gerido está preparado, mas fechado por `EDITORIAL_CONTENT_READY=false`.

### Sugestoes

- Separar "conteudo editorial" de "ferramentas pessoais".
- Usar a exposicao como entrada emocional e cultural.
- Usar podcast e videos como aprofundamento.
- Adicionar testemunhos apenas com consentimento claro.
- Criar moderacao antes de qualquer partilha publica.

### Sala anonima

Estado:

- Qualquer pessoa pode partilhar anonimamente.
- O sistema atribui um nome aleatorio por sessao, por exemplo `Guerreiro238`.
- A versao atual guarda apenas no navegador e permite eliminar cada partilha.
- Uma versao publica exige moderacao, regras claras e protecao contra abuso.

Riscos:

- Partilhas com dados pessoais.
- Pedidos urgentes de ajuda sem resposta.
- Conteudo ofensivo ou gatilhos.
- Responsabilidade da moderacao.

Recomendacao:

- Manter como prototipo local ate existir equipa de moderacao.
- Se ficar online, comecar com partilhas submetidas para aprovacao.

## 9. Ajuda

### Objetivo

Dar acesso rapido a reunioes, contactos, centros, linhas de apoio e recursos presenciais.

### Estado atual

- A secao Ajuda existe na app.
- O botao SOS abre contactos acionaveis e uma mensagem curta para pedir companhia.
- A lista estatica distingue contactos oficiais de horarios indicados pela comunidade.
- O diretorio gerido, com fonte e prazo de revisao, esta implementado mas fechado por `HELP_DIRECTORY_READY=false`.

### Sugestoes

- Separar por ilha/cidade.
- Mostrar horarios, morada, contactos, tipo de reuniao e observacoes.
- Incluir botao "pedir ajuda agora".
- Incluir aviso de emergencia quando houver risco imediato.
- Validar todos os contactos antes de publicar.

### Dados recomendados para reunioes

```json
{
  "name": "Grupo So Por Hoje",
  "island": "Santiago",
  "city": "Praia",
  "address": "A validar",
  "weekday": "Terça-feira",
  "time": "19:00",
  "contact": "+238...",
  "notes": "Aberta/fechada, presencial/online"
}
```

### Decisoes a validar

- Quem mantem a lista atualizada?
- Como confirmar que um grupo continua ativo?
- Como lidar com contactos pessoais?
- Deve existir formulario para sugerir nova reuniao?

## 10. Notificacoes

### Objetivo

Lembrar a pessoa da meditacao diaria e de momentos de cuidado sem ser invasivo.

### Estado atual

- O lembrete local respeita a hora escolhida enquanto a aplicacao esta aberta.
- Cliente, preferencias, subscricao, service worker e emissor de Web Push estao preparados.
- O ecrã bloqueado recebe apenas uma mensagem generica, sem dados da Jornada.
- Web Push permanece fechado por `PUSH_DELIVERY_READY=false` ate configurar VAPID, cron e testes em dois dispositivos.
- Email diario, WhatsApp e Telegram nao fazem parte do fluxo atual.

### Sugestoes

- Comecar com notificacao local do browser.
- Permitir escolher horario.
- Texto curto e respeitoso.
- Botao claro para desativar.

Exemplo:

```text
So por hoje: a meditacao do dia esta disponivel.
```

## 11. Partilha

### Objetivo

Permitir partilhar a meditacao no formato usado pelo grupo, sem alterar o conteudo oficial.

### Estado atual

- Existe botao de partilha com icone.
- A mensagem inclui saudacao, data, titulo, corpo, reflexao "So por hoje", dominio curto, fonte e permissao.
- O URL da pagina da fonte nao entra no texto copiado, evitando duplicacao automatica de previews no Messenger.

### Sugestoes

- Copiar texto para clipboard quando Web Share API nao estiver disponivel.
- Criar preview antes de partilhar.
- Permitir partilha de link da pagina.
- Garantir que a fonte oficial vai no fim.

Formato recomendado:

```text
BOM DIA GUERREIROS

MEDITACAO DO DIA

Terça-feira, 02 de Junho de 2026


TITULO


[texto oficial intacto]


SO POR HOJE:

[reflexao oficial]

soporhoje.cv


Fonte oficial: Narcoticos Anonimos Portugal
© NA World Services, Inc. Reprinted by permission.
```

O gerador preserva duas linhas vazias antes do titulo, antes do corpo, antes de `SO POR HOJE` e antes do dominio/fonte conforme o formato aprovado para o grupo.

## 12. Conteudo complementar inteligente

### Objetivo

Gerar atividades, frases e desafios alinhados com a meditacao do dia e o estado da pessoa.

### Estado implementado

- Catálogo local com quatro estados para os 366 dias, disponível sem conta e offline.
- A atividade e o desafio referem o título exato da meditação; testes exigem pelo menos 340 combinações distintas por estado e respeitam os limites de apresentação.
- O catálogo local é distribuído pelo cache versionado da PWA, sem uma segunda cópia persistente por dia no navegador.
- OpenAI fechada por defeito através de `AI_DELIVERY_READY=false`.
- Quando ativada, exige sessão Supabase válida e quota diária atómica por conta.
- A identidade da conta não é enviada à OpenAI; falhas regressam ao catálogo local.

### Regras importantes

- Nao substituir tecnico de saude.
- Nao diagnosticar.
- Nao dar conselho medico.
- Incentivar reuniao, sponsor, contacto seguro e ajuda presencial.
- Em caso de risco, orientar para apoio imediato.

### Sugestoes por estado

Firme:

- Atividade leve.
- Gratidao.
- Partilha positiva.

Preciso de serenidade:

- Respiracao curta.
- Oracao da Serenidade.
- Contactar alguem seguro.

Estou em risco:

- Sair do isolamento.
- Ligar para alguem agora.
- Ir a uma reuniao ou espaco seguro.

Voltei a consumir:

- Linguagem sem culpa.
- Recomecar hoje.
- Procurar ajuda.
- Evitar isolamento.

## 13. Expo

### Objetivo

Transformar a pagina `/expo` numa pagina viva da exposicao, com catalogo, colecoes, videos, podcast, exposicoes e contacto do autor.

### Estado atual

- Hero com imagem da pedra "So Por Hoje".
- Menu responsivo.
- Catalogo com colecao 2024.
- Preview da colecao 2026 "Spirit D'Luz".
- Videos e podcast por YouTube.
- Bio e contactos do autor.

### Sugestoes

- Manter hero visual e direto.
- Usar catalogo/colecoes em vez de "obras" quando o foco for curatorial.
- Criar pagina individual para cada colecao no futuro.
- Adicionar imprensa, recortes e fotos de abertura.
- Adicionar ficha tecnica da exposicao.
- Adicionar formulario de convite/parceria.

### Estrutura futura sugerida

- `/expo`
- `/expo/colecoes/2024-sobriu`
- `/expo/colecoes/2026-spirit-dluz`
- `/expo/imprensa`
- `/expo/contacto`

## 14. Administracao

### Objetivo

Permitir que a equipa mantenha conteudos sem depender sempre de programador.

### Estado atual

- Login individual por código para contas previamente autorizadas.
- Papéis separados para moderação, diretório de ajuda, conteúdo e administração.
- Edição, verificação e retirada de reuniões e centros.
- Fila de moderação para partilhas da comunidade.
- Resumo sanitizado do histórico de envios, sem destinos nem conteúdo privado.
- Auditoria atómica das decisões editoriais, sem copiar conteúdo privado.
- Catálogo de Viver Saudável com rascunho, publicação, retirada e fallback para o conteúdo estático.

### Funcionalidades futuras

- Importar meditações pelo painel com validação restrita.
- Importar e organizar coleções completas da exposição.

### Sugestao de prioridade

1. Testar o painel de Ajuda/reuniões e moderação com contas reais.
2. Testar e ativar o catálogo editorial de vídeos, podcast, exposições e eventos.
3. Painel para coleções completas da exposição.
4. Painel completo de meditações, com permissão restrita.

## 15. Dados e privacidade

### Dados sensiveis

- Data de sobriedade.
- Check-ins.
- Historico de consumo/recaida.
- Partilhas anonimas.
- Numero de telefone.

### Recomendacoes

- Comecar com armazenamento local.
- Explicar claramente onde os dados ficam.
- Permitir apagar dados.
- Se houver login, guardar o minimo necessario.
- Separar dados pessoais de conteudos publicos.
- Encriptar informacao sensivel em backend.

## 16. Arquitetura tecnica recomendada

### Atual

- Frontend estatico em `public/`.
- Dados de meditacoes em JSON.
- Servidor local simples em Python.
- Preparado para Vercel.
- Branch `dev` para desenvolvimento.
- Branch `production` para deploy.
- Validacao automatica de backend, estrutura web, PWA e cliente de conta em GitHub Actions.
- Vercel como destino de publicacao; GitHub Pages desativado por nao executar a API.

### Estado da evolucao

- A base local, as cinco areas, a PWA parcial, o arquivo e a exportacao/importacao estao implementados.
- A API FastAPI, o esquema Supabase, a conta opcional com sincronizacao e o painel administrativo para o papel `admin` estao ativos em producao; o diretorio, a comunidade moderada, o catálogo editorial, a AI e o Web Push continuam preparados e protegidos pelas respetivas flags.
- O acesso administrativo foi validado com OTP e uma conta real: acesso permitido, suspensao com recusa imediata e restauracao para `active`. O browser continua sem acesso direto a `staff_roles`; o backend usa privilegios SQL explicitos de `service_role`.
- As ativacoes restantes dependem de VAPID/cron, chaves OpenAI, restantes papéis reais da equipa, moderadores, validacao de contactos, revisao juridica e testes em dispositivos.
- App mobile nativa, canais WhatsApp/Telegram/email, loja e doacao nao estao iniciados e exigem decisoes proprias antes de desenvolvimento.

## 17. Riscos

- Direitos de autor das meditacoes.
- Dados sensiveis de recuperacao.
- Moderacao de partilhas anonimas.
- Expectativa de suporte em crise.
- Conteudos de saude mental sem validacao tecnica.
- Dependencia de plataformas externas como Meta, YouTube e WhatsApp.

## 18. Recomendacoes imediatas

1. Validar juridicamente a exibicao das meditacoes oficiais e a politica de privacidade preliminar.
2. Confirmar diretamente os contactos e responsáveis dos recursos de Ajuda; os horários existentes ficam aceites provisoriamente e editáveis, mas recursos sem horário ou contacto suficiente continuam em rascunho.
3. Criar o projeto Supabase de Preview, aplicar o esquema e testar RLS com duas contas.
4. Configurar Email OTP, SMTP e CAPTCHA sem enviar segredos por mensagens ou guardar no Git.
5. Definir substitutos, escalas e procedimentos para privacidade, suporte, moderacao e incidentes; Viver Saudável, em `viversaudavel@soporhoje.cv`, e o contacto responsavel comum registado em `OPERATIONS_DECISIONS.md`.
6. Testar PWA, atualizacao, VoiceOver/TalkBack e Web Push em dispositivos reais.
7. Rever o catálogo editorial e o conteudo complementar com autoria, consentimento e apoio clinico/comunitario.
8. Ativar cada flag primeiro em Preview; promover para producao apenas depois da checklist respetiva.

## 19. Perguntas para a equipa

- Quem e responsavel pela manutencao da lista de Ajuda?
- Queremos permitir contas de utilizador nesta fase?
- A sala anonima sera privada, local ou publica?
- Quem modera conteudos publicos?
- Que conteudos precisam de aprovacao antes de publicar?
- A app deve falar mais como ferramenta espiritual, comunitaria ou institucional?
- Que parcerias oficiais devem aparecer?
- Qual e o limite entre inspiracao e aconselhamento?

## 20. Roadmap sugerido

### Curto prazo

- Confirmar Ajuda e concluir revisoes juridica, editorial e de acessibilidade em dispositivos.
- Monitorizar Supabase/OTP, sincronizacao e eliminacao agora ativos em producao.
- Monitorizar o painel administrativo ativo; os quatro papéis foram ensaiados com contas reais, isolamento por área e remoção das permissões temporárias.

### Medio prazo

- Ativar, uma por vez, o diretorio de Ajuda e o catálogo editorial em Preview.
- Configurar e testar Web Push e AI com limites, custos e observabilidade.
- Abrir comunidade apenas depois de equipa, regras, retencao e protocolo de crise aprovados.

### Longo prazo

- App mobile.
- Integracoes com canais, se houver operacao e consentimento adequados.
- Dashboard de impacto.
- Loja e doacao apenas com entidade, pagamentos, entregas, devolucoes e transparencia definidos.

## 21. Criterios de sucesso

- A meditacao diaria aparece todos os dias sem falhas.
- A pessoa consegue ler, marcar como lida e partilhar em poucos segundos.
- A pessoa encontra ajuda presencial rapidamente.
- A Jornada motiva sem gerar culpa.
- A equipa consegue atualizar informacoes essenciais.
- A plataforma cresce sem duplicar conteudos.

## 22. Arquitetura funcional aprovada

O mapa funcional apresentado pela equipa passa a orientar a evolucao da plataforma. A navegacao principal fica organizada em cinco eixos:

1. **Meditacao**: meditacao do dia, reflexao, atividade, frase, desafio, gratidao, ferramentas e historico de leitura.
2. **Jornada**: dias limpos, check-in diario, historico, marcos, estatisticas e definicoes pessoais.
3. **Viver Saudavel**: podcast, historias, informacao pratica, arte, exposicao, conteudos educativos e recursos uteis.
4. **Ajuda**: pedido imediato de apoio, reunioes, servicos, recursos de emergencia e futura sala anonima moderada.
5. **Sobre**: projeto, historia, exposicao, equipa, parceiros, privacidade, contactos e perguntas frequentes.

### Estado por bloco

| Bloco | Estado atual | Proximo passo |
| --- | --- | --- |
| Meditacao | Funcional, com gratidao diaria | Rever conteudo complementar com equipa clinica/comunitaria |
| Jornada | Funcional no dispositivo e com sincronizacao opcional ativa no Supabase | Monitorizar conflitos e manter testes de regressao com duas contas |
| Viver Saudavel | Podcast, documentario, historia do projeto, exposicao e recursos educativos | Adicionar novos testemunhos apenas com consentimento |
| Catálogo editorial | Gestão por rascunho/publicação preparada e fechada por flag | Testar o papel `content_editor` em Preview e rever autoria/consentimento |
| Ajuda | Fluxo SOS, contactos oficiais acionaveis e estado de verificacao por recurso | Horários existentes aceites provisoriamente e editáveis; confirmar contactos e completar recursos sem dados suficientes |
| Sala anonima | Diário local ativo; backend e cliente público moderado preparados atrás de `COMMUNITY_READY=false` | Não ativar sem equipa, regras, retenção e protocolo de crise |
| Sobre | Missao, visao, historia, coordenacao, privacidade, contactos e FAQ | Identificar parceiros apenas depois de confirmacao |
| Conta/login | Email OTP e escolha de sincronizacao ativos em producao | Monitorizar entrega SMTP, CAPTCHA, RLS e erros de sincronizacao |
| Notificacoes push | Cliente, emissor protegido, fusos horarios, cancelamento e service worker preparados atras de feature flag | Configurar VAPID e Supabase Cron; testar em dois dispositivos antes de ativar a flag |
| PWA | Instalacao, atalhos e fallbacks offline separados para app, privacidade e exposicao | Verificar instalacao e atualizacao do service worker em producao |
| Loja e doacao | Nao iniciado | Definir operacao, pagamentos, entregas e transparencia |
| Privacidade e seguranca | Politica preliminar, exportacao e eliminacao local, remota e da conta, API administrativa protegida e cabecalhos web implementados | Revisao juridica e validacao de conformidade |

### Ordem de desenvolvimento

**Fase A - Estrutura e conteudo seguro**

- Consolidar as cinco secoes principais.
- Fechar Meditacao, Jornada, Viver Saudavel, Ajuda e Sobre.
- Validar contactos e informacao de apoio.
- Publicar politica de privacidade e limites da plataforma.

**Fase B - Aplicacao instalavel**

- Transformar a interface em PWA.
- Criar funcionamento offline parcial.
- Implementar notificacoes com consentimento e preferencias de horario.

**Fase C - Conta e sincronizacao**

- Conta opcional com codigo de acesso por email.
- Importar os dados locais quando a pessoa criar conta.
- Sincronizar apenas os dados necessarios entre dispositivos.
- Esquema inicial e politicas RLS definidos em `supabase/schema.sql`.

**Fase D - Comunidade e sustentabilidade**

- Sala anonima real com denuncia, moderacao e resposta a crise.
- Loja e doacao com regras financeiras e operacionais definidas.
- Parcerias, voluntariado e transparencia sobre o uso do apoio.

### Decisoes de seguranca

- A Sala Anonima atual permanece local e deve dizer claramente que nao e uma conversa com outras pessoas.
- O backend moderado já está preparado mas fechado por `COMMUNITY_READY=false`: toda partilha entra pendente, o pseudónimo nasce no servidor, a leitura pública omite identidade e a moderação exige acesso administrativo.
- O cliente comunitário também está preparado atrás da mesma flag: leitura pública mínima, envio e denúncia autenticados e renderização de texto sem HTML dinâmico.
- O diretório de ajuda gerido contém 17 recursos e continua fechado por `HELP_DIRECTORY_READY=false`: 10 foram aceites provisoriamente e verificados até 28 de dezembro de 2026; 7 reuniões permanecem em rascunho por falta de horário ou contacto suficiente. Qualquer alteração regressa a rascunho e contactos vencidos desaparecem da listagem.
- Os modais isolam o fundo, mantêm o foco por teclado, fecham com `Escape` e devolvem o foco à origem; check-ins e feedback dinâmico expõem estados às tecnologias assistivas.
- O botao SOS deve encaminhar para ajuda humana e nunca simular atendimento clinico.
- Login, sincronizacao e notificacoes so avancam depois de politica de privacidade e modelo de dados minimos.
- Loja e doacao nao entram como botoes inativos; entram apenas quando os fluxos reais estiverem definidos.
