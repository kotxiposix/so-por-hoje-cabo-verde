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
```

A URL e a chave publica podem ser usadas pelo cliente depois de as regras RLS estarem ativas. A `SERVICE_ROLE_KEY` ignora RLS e fica exclusivamente no ambiente seguro da Vercel.

## 2. Modelo minimo

- `journey_state`: um documento JSON por conta; apenas o proprio utilizador pode ler e atualizar.
- `anonymous_posts`: novas partilhas entram sempre como `pending`.
- `anonymous_reports`: uma denuncia por utilizador e publicacao.
- `help_resources`: o publico ve apenas recursos marcados como verificados.

O browser nao recebe permissoes para publicar diretamente, moderar, apagar mensagens de outras pessoas ou alterar recursos de ajuda. Essas operacoes pertencem a funcoes de servidor e a uma area administrativa protegida.

## 3. Migracao dos dados locais

Ao criar conta, a interface deve:

1. mostrar exatamente quais dados serao sincronizados;
2. pedir consentimento;
3. importar `sph-progress` uma unica vez;
4. manter uma copia local para funcionamento offline;
5. resolver conflitos pelo `updated_at`, oferecendo escolha quando ambos os lados mudaram.

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

## 5. API e OpenAI na Vercel

`api/index.py` expõe a aplicacao FastAPI como funcao Python. `vercel.json` envia `/api/*` para essa funcao antes das rotas estaticas.

Variaveis privadas na Vercel:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

Nunca colocar a chave OpenAI nem a service role do Supabase em `public/`, no Git ou em JavaScript enviado ao navegador.

## 6. Checklist antes de producao

- Politica de privacidade aprovada e publicada.
- SMTP e remetente validados.
- CAPTCHA ativo no acesso por email.
- RLS testada com dois utilizadores diferentes.
- Moderadores e protocolo de crise definidos.
- Contactos de ajuda confirmados por fonte responsavel.
- Registos tecnicos sem texto sensivel das partilhas.
- Processo de exportacao e eliminacao de conta testado.
