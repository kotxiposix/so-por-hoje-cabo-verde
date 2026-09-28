# Modelo de email OTP

Usar em `Authentication > Email Templates > Magic Link` no Supabase depois de configurar SMTP próprio.

Remetente aprovado para os códigos de acesso:

```text
Só Por Hoje Viver Saudável <viversaudavel@soporhoje.cv>
```

O endereço recebe mensagens através do Cloudflare Email Routing e está verificado como remetente na conta Google do projeto. O encaminhamento de entrada não substitui o SMTP de saída exigido pelo Supabase.

## Assunto

```text
O teu código de acesso · Só Por Hoje Cabo Verde
```

## Corpo HTML

```html
<!doctype html>
<html lang="pt">
  <body style="margin:0;background:#f4f8fa;color:#0b3555;font-family:Arial,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f8fa;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:520px;background:#ffffff;border:1px solid #d7e3e9;border-radius:8px;">
            <tr>
              <td style="padding:32px;">
                <p style="margin:0 0 8px;color:#168aa4;font-size:13px;font-weight:700;text-transform:uppercase;">Só Por Hoje Cabo Verde</p>
                <h1 style="margin:0 0 16px;font-size:26px;line-height:1.25;">Código de acesso</h1>
                <p style="margin:0 0 24px;color:#40566a;font-size:16px;line-height:1.6;">Introduz este código na plataforma para concluir o acesso:</p>
                <p style="margin:0 0 24px;padding:18px;background:#eef8fa;border-radius:8px;text-align:center;font-size:32px;font-weight:700;letter-spacing:6px;">{{ .Token }}</p>
                <p style="margin:0;color:#647789;font-size:14px;line-height:1.6;">Se não pediste este código, ignora esta mensagem. Nunca partilhes o código com outra pessoa.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
```

## Validação obrigatória

1. Confirmar que o email mostra apenas o código de seis dígitos e não um magic link.
2. Desativar link tracking no fornecedor SMTP.
3. Testar em Gmail, Outlook e num endereço fora da equipa Supabase.
4. Confirmar que um pedido repetido para o mesmo email respeita a janela mínima configurada.
5. Não aumentar limites antes de validar Turnstile, logs e alertas de abuso.

O modelo não inclui publicidade, conteúdos de recuperação, dados da Jornada nem imagens externas.
