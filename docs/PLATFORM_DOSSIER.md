# Dossie de Documentacao da Plataforma

## So Por Hoje Cabo Verde

Este documento serve para alinhar equipa, parceiros e decisores sobre a evolucao da plataforma So Por Hoje Cabo Verde. O objetivo e juntar num unico sitio a visao funcional, as decisoes tecnicas, as sugestoes de experiencia de utilizador e os pontos que precisam de validacao antes de crescer.

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
- Recuperacao
- Ajuda

Funcoes principais:

- Mostrar a meditacao diaria.
- Marcar meditacao como lida.
- Abrir Oracao da Serenidade.
- Partilhar texto no formato do grupo.
- Ativar notificacao.
- Ver atividade do dia, frase do dia e desafio mental.
- Acompanhar dias limpos/sobrios.
- Fazer check-in pessoal.
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

### Sugestoes

- Manter o texto da meditacao intacto.
- Separar claramente conteudo oficial de reflexoes, atividades e desafios criados pela plataforma.
- Criar estado offline para quando a internet falhar.
- Permitir consultar meditacoes por data no futuro.
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

### Decisoes a validar

- Guardar dados apenas no dispositivo ou permitir conta?
- Se houver login, usar telefone/token, email ou outra opcao?
- Que dados nunca devem ser recolhidos?
- Como apagar dados pessoais facilmente?

## 8. Recuperacao

### Objetivo

Reunir conteudos de inspiracao, exposicao, podcast, testemunhos e partilhas que ajudem a pessoa a continuar.

### Estado atual

- Existe secao da exposicao dentro da app.
- A pagina `/expo` apresenta catalogo, videos, podcast, exposicoes, bio e contacto.
- Existe sala anonima em prototipo na app principal.

### Sugestoes

- Separar "conteudo editorial" de "ferramentas pessoais".
- Usar a exposicao como entrada emocional e cultural.
- Usar podcast e videos como aprofundamento.
- Adicionar testemunhos apenas com consentimento claro.
- Criar moderacao antes de qualquer partilha publica.

### Sala anonima

Ideia:

- Qualquer pessoa pode partilhar anonimamente.
- O sistema atribui um nome aleatorio por sessao, por exemplo `Guerreiro238`.
- A primeira versao pode guardar apenas no navegador.
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
- Foram pensados centros e reunioes em Cabo Verde para validacao.

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

### Abordagens possiveis

- Browser push notifications.
- PWA instalada no Android.
- Notificacoes no iOS via PWA, com limitacoes.
- Email diario.
- WhatsApp/Telegram no futuro.

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
- A mensagem pode ser formatada com data, titulo, corpo e "So por hoje".

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

Fonte oficial: Narcoticos Anonimos Portugal
© NA World Services, Inc. Reprinted by permission.
https://na-pt.erlog.pt/sph.php
```

## 12. Conteudo complementar inteligente

### Objetivo

Gerar atividades, frases e desafios alinhados com a meditacao do dia e o estado da pessoa.

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

### Funcionalidades futuras

- Login de administrador.
- Editar reunioes e centros.
- Importar meditacoes.
- Validar conteudo antes de publicar.
- Ver historico de envios.
- Testar envio para canais.
- Gerir videos, podcast e eventos.

### Sugestao de prioridade

1. Painel simples para Ajuda/reunioes.
2. Painel para conteudos da expo.
3. Painel para logs de envio.
4. Painel completo de meditacoes, com permissao restrita.

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

### Evolucao sugerida

Fase 1:

- Continuar estatico com dados locais.
- Melhorar UX e conteudo.
- Validar lista de ajuda.

Fase 2:

- Backend leve com API.
- Base de dados PostgreSQL/Supabase.
- Autenticacao opcional.
- Painel administrativo.

Fase 3:

- PWA completa.
- Notificacoes push.
- Scheduler de envios.
- Integracoes WhatsApp/Telegram/email.

Fase 4:

- App mobile.
- Conteudo audio/video estruturado.
- Sala anonima moderada.
- Relatorios e impacto comunitario.

## 17. Riscos

- Direitos de autor das meditacoes.
- Dados sensiveis de recuperacao.
- Moderacao de partilhas anonimas.
- Expectativa de suporte em crise.
- Conteudos de saude mental sem validacao tecnica.
- Dependencia de plataformas externas como Meta, YouTube e WhatsApp.

## 18. Recomendacoes imediatas

1. Validar juridicamente a exibicao das meditacoes oficiais.
2. Validar lista de reunioes e centros em Cabo Verde.
3. Definir politica de privacidade simples.
4. Criar texto claro: "nao substitui ajuda profissional".
5. Fechar MVP da app principal.
6. Melhorar pagina `/expo` como pagina publica institucional.
7. Decidir se a Jornada fica so local ou com login.
8. Preparar conteudo para primeira versao PWA.

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

- Ajustar UX da meditacao.
- Fechar Jornada com dias limpos e check-in.
- Melhorar Ajuda com dados validados.
- Consolidar Expo.
- Publicar politica de privacidade.

### Medio prazo

- PWA instalavel.
- Notificacoes.
- Painel simples.
- Reunioes atualizaveis.
- Conteudo audio.

### Longo prazo

- App mobile.
- Login seguro.
- Sala anonima moderada.
- Integracoes com canais.
- Dashboard de impacto.

## 21. Criterios de sucesso

- A meditacao diaria aparece todos os dias sem falhas.
- A pessoa consegue ler, marcar como lida e partilhar em poucos segundos.
- A pessoa encontra ajuda presencial rapidamente.
- A Jornada motiva sem gerar culpa.
- A equipa consegue atualizar informacoes essenciais.
- A plataforma cresce sem duplicar conteudos.

