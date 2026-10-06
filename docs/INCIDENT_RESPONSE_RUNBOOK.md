# Resposta a incidentes

Estado: **rascunho operacional**. Este roteiro não aprova a ativação de Push, AI, comunidade, diretório gerido ou conteúdo editorial. Antes dessas ativações, a equipa ainda precisa de nomear um substituto, aprovar tempos de resposta e ensaiar os cenários aplicáveis.

Contacto responsável: **Viver Saudável — viversaudavel@soporhoje.cv**.

Não guardar neste ficheiro nomes pessoais, credenciais, tokens, textos da Jornada, partilhas da comunidade ou documentos recebidos. A identificação do substituto, a escala e os contactos internos ficam num registo privado com acesso controlado.

## 1. Classificar

| Nível | Exemplo | Ação inicial |
| --- | --- | --- |
| Crítico | acesso entre contas, chave privada exposta, conta administrativa comprometida ou dados pessoais publicados | conter imediatamente e chamar responsável e substituto |
| Alto | push após cancelamento, contacto de emergência incorreto ou publicação sem consentimento | desligar a função afetada e iniciar análise no próprio dia |
| Normal | falha sem exposição de dados, indisponibilidade do serviço ou informação desatualizada sem risco imediato | registar, corrigir e acompanhar no ciclo operacional |

Quando houver dúvida, tratar inicialmente como o nível mais alto plausível.

## 2. Receber e registar

1. Registar data e hora, origem do alerta, funcionalidade afetada e uma referência técnica mínima.
2. Não copiar conteúdo privado para o registo. Usar identificadores abreviados, contagens e códigos de resposta quando bastarem.
3. Confirmar quem assume a coordenação. Se o responsável não responder no tempo aprovado, chamar o substituto registado em privado.
4. Abrir uma linha cronológica simples com decisão, autor da decisão, hora e resultado.

## 3. Conter

Usar primeiro a medida que interrompe o risco com menor impacto:

- conta ou sincronização: definir `ACCOUNT_READY=false`;
- área da equipa: definir `STAFF_ACCESS_READY=false` e suspender o papel comprometido;
- AI: definir `AI_DELIVERY_READY=false`;
- Push: definir `PUSH_DELIVERY_READY=false` e parar o agendamento;
- comunidade: definir `COMMUNITY_READY=false` e ocultar a publicação afetada;
- diretório gerido: definir `HELP_DIRECTORY_READY=false`, preservando o catálogo local;
- conteúdo editorial: definir `EDITORIAL_CONTENT_READY=false` e retirar o item afetado.

Se uma credencial puder estar exposta, revogá-la ou rodá-la no fornecedor, atualizar apenas os ambientes necessários e confirmar que o valor antigo deixou de funcionar. Nunca colocar a credencial num ticket, email ou captura de ecrã.

## 4. Investigar com evidência mínima

Recolher apenas o necessário para responder:

- intervalo temporal;
- ambiente e versão do deploy;
- endpoint ou função afetada;
- código de resposta e referência técnica sanitizada;
- número aproximado de contas ou registos potencialmente afetados;
- alterações de configuração e auditoria da equipa relacionadas.

Não exportar bases completas por conveniência. Não copiar check-ins, gratidões, textos da Jornada, partilhas ou notas de moderação para logs de incidente.

## 5. Corrigir e recuperar

1. Corrigir a causa e adicionar teste automático quando for tecnicamente reproduzível.
2. Validar primeiro em ambiente isolado ou Preview.
3. Confirmar que a contenção continua ativa durante o teste.
4. Restaurar a função apenas com decisão explícita, responsável disponível e critérios da checklist cumpridos.
5. Vigiar erros, auditoria e comportamento durante o período definido pela equipa.

## 6. Comunicar

- A comunicação interna deve indicar o que aconteceu, impacto conhecido, contenção, próximo passo e responsável, sem reproduzir dados privados.
- Qualquer comunicação a pessoas afetadas, autoridades ou fornecedores deve seguir revisão jurídica adequada a Cabo Verde.
- Não afirmar ausência de impacto enquanto a investigação não a sustentar.
- Um contacto de ajuda incorreto deve ser retirado imediatamente; a confirmação com a entidade acontece antes de nova publicação.

## 7. Rever depois do incidente

Registar causa, alcance, decisões, tempos, correção, testes e ações preventivas. Atualizar este roteiro e a checklist quando necessário. A revisão não deve incluir conteúdo privado.

## 8. Ensaio antes da ativação

Executar um exercício fictício para cada função a abrir:

- [ ] conta da equipa comprometida;
- [ ] chave ou segredo exposto;
- [ ] acesso cruzado entre duas contas;
- [ ] publicação com dados pessoais;
- [ ] contacto de ajuda incorreto ou indisponível;
- [ ] push duplicado ou enviado depois do cancelamento;
- [ ] conteúdo publicado sem consentimento válido.

Para cada exercício, confirmar receção, classificação, contenção, evidência mínima, comunicação, recuperação e revisão. Só marcar como concluído depois de o substituto e os tempos de resposta estarem aprovados.
