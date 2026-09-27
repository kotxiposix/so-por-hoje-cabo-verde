# Decisões operacionais antes da ativação

Este documento é um modelo de trabalho para a equipa. Preenchê-lo não ativa qualquer funcionalidade. As flags permanecem fechadas até as decisões serem aprovadas, testadas em Preview e registadas na checklist.

Não guardar aqui números pessoais, chaves, tokens, dados clínicos ou informação de utilizadores. Contactos internos e escalas detalhadas devem ficar num registo privado com acesso controlado.

## 1. Responsabilidade

| Função | Responsável aprovado | Substituto | Canal privado de contacto | Estado |
| --- | --- | --- | --- | --- |
| Responsável da plataforma | Por definir | Por definir | Registo privado | Pendente |
| Privacidade e pedidos de dados | Por definir | Por definir | Registo privado | Pendente |
| Coordenação de moderação | Por definir | Por definir | Registo privado | Pendente |
| Verificação do diretório de ajuda | Por definir | Por definir | Registo privado | Pendente |
| Publicação editorial | Por definir | Por definir | Registo privado | Pendente |
| Incidentes técnicos | Por definir | Por definir | Registo privado | Pendente |

Critério de aprovação: cada função sensível tem responsável e substituto identificados fora do repositório.

## 2. Comunidade moderada

### Cobertura

- Número mínimo de moderadores ativos: **por definir**.
- Horário de cobertura: **por definir**.
- Tempo-alvo para rever uma partilha pendente: **por definir**.
- Tempo-alvo para rever uma denúncia: **por definir**.
- Procedimento quando não há cobertura: **por definir**.

### Decisões permitidas pelo sistema

- `pending → published`: publicar apenas depois de revisão humana.
- `pending → rejected`: rejeitar conteúdo que não possa ser publicado.
- `pending/published → hidden`: retirar conteúdo que exija contenção ou nova análise.
- Conteúdo rejeitado ou ocultado não pode ser republicado silenciosamente.

### Regras a aprovar

- [ ] Proibir nomes, telefones, emails, moradas, ligações e identificação de terceiros.
- [ ] Proibir assédio, ameaças, promoção de consumo, publicidade e spam.
- [ ] Definir tratamento de relatos de consumo sem linguagem de culpa.
- [ ] Definir tratamento de conteúdo potencialmente desencadeador.
- [ ] Definir quando uma publicação pode ser editada, resumida ou apenas rejeitada.
- [ ] Definir como responder a pedidos de eliminação e denúncias.
- [ ] Publicar regras em linguagem simples antes de receber partilhas.

O filtro técnico de contactos é apenas uma barreira adicional. A decisão continua humana.

## 3. Conteúdo de risco

Este protocolo deve ser revisto por pessoas com experiência clínica e comunitária em Cabo Verde antes da abertura.

Princípios já definidos:

- A plataforma não presta atendimento de emergência.
- O moderador não diagnostica, não promete confidencialidade absoluta e não substitui serviços profissionais.
- Uma partilha pública nunca deve expor dados pessoais para tentar organizar ajuda.
- A orientação deve encaminhar para apoio humano verificado, urgência presencial ou pessoa segura conforme a situação.
- Não apresentar a comunidade como monitorizada em tempo real quando isso não estiver garantido.

Decisões pendentes:

- [ ] Definir sinais que exigem ocultação imediata e escalamento.
- [ ] Definir quem recebe o escalamento e por qual canal privado.
- [ ] Confirmar contactos oficiais a usar em situação de perigo.
- [ ] Preparar respostas operacionais curtas, revistas e não clínicas.
- [ ] Ensaiar o protocolo com cenários fictícios, sem dados reais.
- [ ] Definir como registar o incidente sem copiar o texto privado para logs ou auditoria.

## 4. Retenção e eliminação

Nenhum prazo deve ser escolhido apenas por conveniência técnica. A equipa deve obter revisão jurídica adequada a Cabo Verde.

| Tipo de dado | Finalidade | Prazo aprovado | Eliminação/anonimização | Responsável | Estado |
| --- | --- | --- | --- | --- | --- |
| Jornada sincronizada | Sincronização escolhida pela pessoa | Por definir | Eliminação pela pessoa/conta | Por definir | Pendente |
| Partilha pendente | Revisão de moderação | Por definir | Por definir | Por definir | Pendente |
| Partilha publicada | Comunidade | Por definir | Ocultar/eliminar conforme política | Por definir | Pendente |
| Partilha rejeitada/oculta | Segurança e recurso | Por definir | Por definir | Por definir | Pendente |
| Denúncia | Moderação e prevenção de abuso | Por definir | Por definir | Por definir | Pendente |
| Auditoria da equipa | Responsabilização mínima | Por definir | Por definir | Por definir | Pendente |
| Contador diário AI/comunidade | Aplicar limites | Por definir | Eliminação agregada | Por definir | Pendente |
| Subscrição push | Entregar lembrete consentido | Até cancelamento/expiração | Desativar e eliminar endpoint | Por definir | Pendente |

## 5. Diretório de ajuda

- [ ] Confirmar nome, âmbito, ilha/município, telefone, horário e fonte com cada entidade.
- [ ] Definir prazo de revisão por categoria e nível de risco.
- [ ] Definir responsável e substituto pela revisão.
- [ ] Definir como reagir a contacto indisponível ou informação contraditória.
- [ ] Testar que recursos vencidos desaparecem da API pública.
- [ ] Não marcar como emergência um recurso sem telefone confirmado.

O catálogo inicial entra sempre como rascunho. Uma alteração retira a verificação até nova revisão.

## 6. Conteúdo editorial e consentimento

Para cada vídeo, podcast, testemunho, fotografia ou evento:

- [ ] Confirmar autoria e titularidade.
- [ ] Guardar prova de consentimento num arquivo privado apropriado.
- [ ] Confirmar permissão de imagem e voz das pessoas identificáveis.
- [ ] Rever título, resumo, ligação HTTPS, data e imagem de capa.
- [ ] Definir responsável por correções ou retirada.
- [ ] Não publicar testemunhos de recuperação sem consentimento claro e revogável.

O repositório guarda apenas metadados editoriais necessários; provas e documentos pessoais não devem entrar no Git.

## 7. Incidentes

| Etapa | Decisão da equipa |
| --- | --- |
| Receção e triagem | Por definir |
| Contenção técnica | Por definir |
| Preservação mínima de evidência | Por definir |
| Comunicação interna | Por definir |
| Comunicação às pessoas afetadas | Por definir após revisão jurídica |
| Correção e recuperação | Por definir |
| Revisão posterior | Por definir |

Cenários mínimos a ensaiar:

- conta da equipa comprometida;
- chave exposta ou configuração indevida;
- acesso cruzado entre duas contas;
- publicação com dados pessoais;
- contacto de ajuda incorreto ou indisponível;
- notificação push duplicada ou enviada depois do cancelamento;
- conteúdo editorial publicado sem consentimento válido.

## 8. Decisão de abertura

Uma funcionalidade sensível só pode avançar para Preview quando:

1. os responsáveis e substitutos estão definidos;
2. as decisões desta área estão aprovadas;
3. os testes técnicos e humanos da checklist foram executados;
4. existe forma de desligar rapidamente a flag correspondente;
5. o resultado e a data do teste foram registados sem dados pessoais.

Produção exige nova decisão explícita depois do período de observação em Preview. Aprovação de uma função não autoriza automaticamente as restantes.
