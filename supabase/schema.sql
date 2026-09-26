-- So Por Hoje Cabo Verde: account sync and moderated community foundation.
-- Run this file in the Supabase SQL editor after reviewing it for the target project.

create extension if not exists pgcrypto;

create table if not exists public.journey_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  payload jsonb not null default '{}'::jsonb,
  schema_version integer not null default 1 check (schema_version > 0),
  updated_at timestamptz not null default now()
);

create table if not exists public.anonymous_posts (
  id uuid primary key default gen_random_uuid(),
  author_id uuid not null references auth.users(id) on delete cascade,
  pseudonym text not null check (char_length(pseudonym) between 3 and 32),
  body text not null check (char_length(body) between 1 and 280),
  status text not null default 'pending'
    check (status in ('pending', 'published', 'hidden', 'rejected')),
  created_at timestamptz not null default now(),
  moderated_at timestamptz,
  moderation_note text
);

create index if not exists anonymous_posts_status_created_idx
  on public.anonymous_posts (status, created_at desc);

create table if not exists public.anonymous_reports (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.anonymous_posts(id) on delete cascade,
  reporter_id uuid not null references auth.users(id) on delete cascade,
  reason text not null check (reason in ('personal_data', 'harassment', 'unsafe', 'spam', 'other')),
  details text check (details is null or char_length(details) <= 500),
  created_at timestamptz not null default now(),
  unique (post_id, reporter_id)
);

create table if not exists public.help_resources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  island text,
  municipality text,
  category text not null,
  description text,
  phone text,
  email text,
  website text,
  schedule jsonb not null default '[]'::jsonb,
  is_emergency boolean not null default false,
  is_verified boolean not null default false,
  verified_at timestamptz,
  updated_at timestamptz not null default now()
);

create table if not exists public.notification_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  enabled boolean not null default false,
  local_time time not null default '07:00',
  timezone text not null default 'Atlantic/Cape_Verde',
  updated_at timestamptz not null default now()
);

create table if not exists public.push_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  endpoint text not null unique,
  p256dh text not null,
  auth_secret text not null,
  user_agent text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.journey_state enable row level security;
alter table public.anonymous_posts enable row level security;
alter table public.anonymous_reports enable row level security;
alter table public.help_resources enable row level security;
alter table public.notification_preferences enable row level security;
alter table public.push_subscriptions enable row level security;

drop policy if exists "Users read their journey" on public.journey_state;
create policy "Users read their journey"
  on public.journey_state for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "Users create their journey" on public.journey_state;
create policy "Users create their journey"
  on public.journey_state for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users update their journey" on public.journey_state;
create policy "Users update their journey"
  on public.journey_state for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "Public reads moderated posts" on public.anonymous_posts;
create policy "Public reads moderated posts"
  on public.anonymous_posts for select
  to anon, authenticated
  using (status = 'published');

drop policy if exists "Members submit pending posts" on public.anonymous_posts;
create policy "Members submit pending posts"
  on public.anonymous_posts for insert
  to authenticated
  with check (
    (select auth.uid()) = author_id
    and status = 'pending'
    and moderated_at is null
    and moderation_note is null
  );

drop policy if exists "Members report published posts" on public.anonymous_reports;
create policy "Members report published posts"
  on public.anonymous_reports for insert
  to authenticated
  with check (
    (select auth.uid()) = reporter_id
    and exists (
      select 1
      from public.anonymous_posts post
      where post.id = post_id and post.status = 'published'
    )
  );

drop policy if exists "Public reads verified help resources" on public.help_resources;
create policy "Public reads verified help resources"
  on public.help_resources for select
  to anon, authenticated
  using (is_verified = true);

drop policy if exists "Users manage notification preferences" on public.notification_preferences;
create policy "Users manage notification preferences"
  on public.notification_preferences for all
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users manage push subscriptions" on public.push_subscriptions;
create policy "Users manage push subscriptions"
  on public.push_subscriptions for all
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

-- Moderation and resource management deliberately have no browser write policy.
-- Use a trusted server process with the Supabase service role for those actions.
