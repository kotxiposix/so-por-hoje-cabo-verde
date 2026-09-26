-- So Por Hoje Cabo Verde: account sync and moderated community foundation.
-- Run this file in the Supabase SQL editor after reviewing it for the target project.

create extension if not exists pgcrypto;

create table if not exists public.journey_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  payload jsonb not null default '{}'::jsonb,
  schema_version integer not null default 1 check (schema_version > 0),
  updated_at timestamptz not null default now()
);

create or replace function public.save_journey_state(
  p_payload jsonb,
  p_schema_version integer,
  p_expected_updated_at timestamptz default null,
  p_force boolean default false
)
returns table(saved boolean, current_updated_at timestamptz)
language plpgsql
security invoker
set search_path = ''
as $$
declare
  current_user_id uuid := auth.uid();
  stored_updated_at timestamptz;
  next_updated_at timestamptz := clock_timestamp();
begin
  if current_user_id is null then
    raise exception 'Authentication required';
  end if;
  if p_schema_version is null
    or p_schema_version < 1
    or p_payload is null
    or jsonb_typeof(p_payload) <> 'object' then
    raise exception 'Invalid journey payload';
  end if;

  select journey.updated_at
    into stored_updated_at
    from public.journey_state as journey
    where journey.user_id = current_user_id
    for update;

  if found then
    if not p_force and (p_expected_updated_at is null or stored_updated_at <> p_expected_updated_at) then
      return query select false, stored_updated_at;
      return;
    end if;

    update public.journey_state
      set payload = p_payload,
          schema_version = p_schema_version,
          updated_at = next_updated_at
      where user_id = current_user_id;
    return query select true, next_updated_at;
    return;
  end if;

  begin
    insert into public.journey_state (user_id, payload, schema_version, updated_at)
    values (current_user_id, p_payload, p_schema_version, next_updated_at);
    return query select true, next_updated_at;
  exception when unique_violation then
    select journey.updated_at
      into stored_updated_at
      from public.journey_state as journey
      where journey.user_id = current_user_id;
    return query select false, stored_updated_at;
  end;
end;
$$;

revoke all on function public.save_journey_state(jsonb, integer, timestamptz, boolean)
  from public, anon;
grant execute on function public.save_journey_state(jsonb, integer, timestamptz, boolean)
  to authenticated;

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
  source_url text,
  verification_status text not null default 'draft',
  verified_at timestamptz,
  review_due_at date,
  updated_at timestamptz not null default now(),
  constraint help_resources_schedule_array_check
    check (jsonb_typeof(schedule) = 'array'),
  constraint help_resources_verification_status_check
    check (verification_status in ('draft', 'verified', 'stale', 'retired'))
);

alter table public.help_resources add column if not exists source_url text;
alter table public.help_resources
  add column if not exists verification_status text not null default 'draft';
alter table public.help_resources add column if not exists review_due_at date;

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'help_resources_verification_status_check'
  ) then
    alter table public.help_resources
      add constraint help_resources_verification_status_check
      check (verification_status in ('draft', 'verified', 'stale', 'retired')) not valid;
  end if;
  if not exists (
    select 1 from pg_constraint where conname = 'help_resources_schedule_array_check'
  ) then
    alter table public.help_resources
      add constraint help_resources_schedule_array_check
      check (jsonb_typeof(schedule) = 'array') not valid;
  end if;
end;
$$;

create index if not exists help_resources_public_idx
  on public.help_resources (is_verified, verification_status, review_due_at, is_emergency, name);

create table if not exists public.notification_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  enabled boolean not null default false,
  local_time time not null default '07:00',
  timezone text not null default 'Atlantic/Cape_Verde',
  last_sent_on date,
  updated_at timestamptz not null default now()
);

alter table public.notification_preferences
  add column if not exists last_sent_on date;

create index if not exists notification_preferences_due_idx
  on public.notification_preferences (enabled, local_time)
  where enabled = true;

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

create table if not exists public.ai_daily_usage (
  user_id uuid not null references auth.users(id) on delete cascade,
  usage_date date not null,
  request_count integer not null default 0 check (request_count >= 0),
  updated_at timestamptz not null default now(),
  primary key (user_id, usage_date)
);

create table if not exists public.community_daily_usage (
  user_id uuid not null references auth.users(id) on delete cascade,
  usage_date date not null,
  post_count integer not null default 0 check (post_count >= 0),
  updated_at timestamptz not null default now(),
  primary key (user_id, usage_date)
);

create or replace function public.claim_ai_daily_request(p_user_id uuid, p_limit integer default 3)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  affected integer;
begin
  if p_limit < 1 then
    return false;
  end if;

  insert into public.ai_daily_usage (user_id, usage_date, request_count, updated_at)
  values (p_user_id, (now() at time zone 'Atlantic/Cape_Verde')::date, 1, now())
  on conflict (user_id, usage_date) do update
    set request_count = public.ai_daily_usage.request_count + 1,
        updated_at = now()
    where public.ai_daily_usage.request_count < p_limit;

  get diagnostics affected = row_count;
  return affected = 1;
end;
$$;

revoke all on function public.claim_ai_daily_request(uuid, integer) from public, anon, authenticated;
grant execute on function public.claim_ai_daily_request(uuid, integer) to service_role;

drop function if exists public.claim_community_daily_post(uuid, integer);

create or replace function public.submit_anonymous_post(
  p_user_id uuid,
  p_pseudonym text,
  p_body text,
  p_limit integer default 3
)
returns setof public.anonymous_posts
language plpgsql
security definer
set search_path = ''
as $$
declare
  affected integer;
begin
  if p_limit < 1
    or char_length(p_pseudonym) not between 3 and 32
    or char_length(p_body) not between 1 and 280 then
    return;
  end if;

  insert into public.community_daily_usage (user_id, usage_date, post_count, updated_at)
  values (p_user_id, (now() at time zone 'Atlantic/Cape_Verde')::date, 1, now())
  on conflict (user_id, usage_date) do update
    set post_count = public.community_daily_usage.post_count + 1,
        updated_at = now()
    where public.community_daily_usage.post_count < p_limit;

  get diagnostics affected = row_count;
  if affected <> 1 then
    return;
  end if;

  return query
    insert into public.anonymous_posts (author_id, pseudonym, body, status)
    values (p_user_id, p_pseudonym, p_body, 'pending')
    returning *;
end;
$$;

revoke all on function public.submit_anonymous_post(uuid, text, text, integer)
  from public, anon, authenticated;
grant execute on function public.submit_anonymous_post(uuid, text, text, integer)
  to service_role;

alter table public.journey_state enable row level security;
alter table public.anonymous_posts enable row level security;
alter table public.anonymous_reports enable row level security;
alter table public.help_resources enable row level security;
alter table public.notification_preferences enable row level security;
alter table public.push_subscriptions enable row level security;
alter table public.ai_daily_usage enable row level security;
alter table public.community_daily_usage enable row level security;

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

drop policy if exists "Users delete their journey" on public.journey_state;
create policy "Users delete their journey"
  on public.journey_state for delete
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "Public reads moderated posts" on public.anonymous_posts;
drop policy if exists "Members submit pending posts" on public.anonymous_posts;
drop policy if exists "Members report published posts" on public.anonymous_reports;

drop policy if exists "Public reads verified help resources" on public.help_resources;

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

-- Community access, moderation and resource management deliberately have no
-- browser policy. Use trusted server endpoints with the service role so feature
-- flags, generated pseudonyms and response shaping cannot be bypassed.
