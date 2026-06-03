# Arquitetura

```text
data/meditations.json
        |
        v
Repositorio de Meditacoes
        |
        v
Servico Diario
        |
        +--> API REST
        |
        +--> Scheduler
                |
                v
             Canais
             - Console
             - Facebook Messenger
             - Email
             - Telegram
             - WhatsApp
```

## Principios

- A meditacao usa `month_day` como chave primaria (`MM-DD`).
- O ano nunca pertence ao conteudo canonico.
- Historico de envios deve usar data completa para auditoria e idempotencia.
- Canais de envio sao adaptadores independentes.
- A API e o scheduler consomem o mesmo servico de dominio.

## Tabelas recomendadas para PostgreSQL

```sql
create table meditations (
  month_day text primary key check (month_day ~ '^\d{2}-\d{2}$'),
  title text not null,
  body text not null,
  reflection text not null,
  language text not null default 'pt-CV',
  status text not null default 'published',
  source text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table channels (
  id uuid primary key,
  type text not null,
  name text not null,
  destination_id text,
  config jsonb not null default '{}',
  enabled boolean not null default true,
  created_at timestamptz not null default now()
);

create table send_logs (
  id uuid primary key,
  send_date date not null,
  month_day text not null references meditations(month_day),
  channel_id uuid references channels(id),
  destination_id text,
  status text not null,
  message_hash text not null,
  error_message text,
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  unique (send_date, channel_id, destination_id)
);
```

