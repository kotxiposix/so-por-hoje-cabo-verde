-- So Por Hoje Cabo Verde: account sync and moderated community foundation.
-- Run this file in the Supabase SQL editor after reviewing it for the target project.

create extension if not exists pgcrypto;

create table if not exists public.staff_roles (
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('admin', 'moderator', 'help_editor', 'content_editor')),
  status text not null default 'active' check (status in ('active', 'suspended')),
  last_edited_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, role)
);

alter table public.staff_roles
  add column if not exists last_edited_by uuid references auth.users(id) on delete set null;

create index if not exists staff_roles_active_idx
  on public.staff_roles (status, role, user_id)
  where status = 'active';

alter table public.staff_roles drop constraint if exists staff_roles_role_check;
alter table public.staff_roles
  add constraint staff_roles_role_check
  check (role in ('admin', 'moderator', 'help_editor', 'content_editor')) not valid;

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
  moderated_by uuid references auth.users(id) on delete set null,
  moderation_note text
);

alter table public.anonymous_posts
  add column if not exists moderated_by uuid references auth.users(id) on delete set null;

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
  last_edited_by uuid references auth.users(id) on delete set null,
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
alter table public.help_resources
  add column if not exists last_edited_by uuid references auth.users(id) on delete set null;

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

create table if not exists public.editorial_content (
  id uuid primary key default gen_random_uuid(),
  kind text not null check (kind in ('podcast', 'video', 'story', 'resource', 'exhibition', 'event')),
  title text not null,
  summary text not null,
  url text,
  image_url text,
  display_date text,
  sort_order integer not null default 0 check (sort_order between -999 and 999),
  status text not null default 'draft' check (status in ('draft', 'published', 'retired')),
  published_at timestamptz,
  last_edited_by uuid references auth.users(id) on delete set null,
  updated_at timestamptz not null default now()
);

create index if not exists editorial_content_public_idx
  on public.editorial_content (status, sort_order, published_at desc);

create table if not exists public.staff_audit_events (
  id bigint generated always as identity primary key,
  actor_id uuid references auth.users(id) on delete set null,
  action text not null check (action in (
    'community.published', 'community.hidden', 'community.rejected',
    'help.created', 'help.updated', 'help.verified', 'help.retired', 'help.stale',
    'content.created', 'content.updated', 'content.published', 'content.retired',
    'staff_role.admin.activated', 'staff_role.admin.suspended',
    'staff_role.moderator.activated', 'staff_role.moderator.suspended',
    'staff_role.help_editor.activated', 'staff_role.help_editor.suspended',
    'staff_role.content_editor.activated', 'staff_role.content_editor.suspended'
  )),
  target_type text not null check (target_type in ('community_post', 'help_resource', 'editorial_content', 'staff_role')),
  target_id uuid not null,
  created_at timestamptz not null default now()
);

create index if not exists staff_audit_events_created_idx
  on public.staff_audit_events (created_at desc, id desc);

alter table public.staff_audit_events drop constraint if exists staff_audit_events_action_check;
alter table public.staff_audit_events
  add constraint staff_audit_events_action_check check (action in (
    'community.published', 'community.hidden', 'community.rejected',
    'help.created', 'help.updated', 'help.verified', 'help.retired', 'help.stale',
    'content.created', 'content.updated', 'content.published', 'content.retired',
    'staff_role.admin.activated', 'staff_role.admin.suspended',
    'staff_role.moderator.activated', 'staff_role.moderator.suspended',
    'staff_role.help_editor.activated', 'staff_role.help_editor.suspended',
    'staff_role.content_editor.activated', 'staff_role.content_editor.suspended'
  )) not valid;
alter table public.staff_audit_events drop constraint if exists staff_audit_events_target_type_check;
alter table public.staff_audit_events
  add constraint staff_audit_events_target_type_check
  check (target_type in ('community_post', 'help_resource', 'editorial_content', 'staff_role')) not valid;

create or replace function public.audit_staff_role_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.last_edited_by is not null
    and (tg_op = 'INSERT' or new.status is distinct from old.status) then
    insert into public.staff_audit_events (actor_id, action, target_type, target_id)
    values (
      new.last_edited_by,
      'staff_role.' || new.role || '.' || new.status,
      'staff_role',
      new.user_id
    );
  end if;
  return new;
end;
$$;

drop trigger if exists staff_roles_audit_trigger on public.staff_roles;
create trigger staff_roles_audit_trigger
after insert or update of status on public.staff_roles
for each row execute function public.audit_staff_role_change();

revoke all on function public.audit_staff_role_change()
  from public, anon, authenticated;

create or replace function public.list_staff_roles(p_actor_id uuid)
returns table(user_id uuid, email text, role text, status text, updated_at timestamptz)
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not exists (
    select 1 from public.staff_roles
    where staff_roles.user_id = p_actor_id
      and staff_roles.role = 'admin'
      and staff_roles.status = 'active'
  ) then
    raise exception 'Actor is not an active administrator';
  end if;

  return query
    select roles.user_id, users.email::text, roles.role, roles.status, roles.updated_at
    from public.staff_roles as roles
    join auth.users as users on users.id = roles.user_id
    order by lower(users.email), roles.role;
end;
$$;

revoke all on function public.list_staff_roles(uuid) from public, anon, authenticated;
grant execute on function public.list_staff_roles(uuid) to service_role;

create or replace function public.manage_staff_role(
  p_actor_id uuid,
  p_email text,
  p_role text,
  p_status text
)
returns table(user_id uuid, email text, role text, status text, updated_at timestamptz)
language plpgsql
security definer
set search_path = ''
as $$
declare
  target_user_id uuid;
  active_admins integer;
begin
  if not exists (
    select 1 from public.staff_roles
    where staff_roles.user_id = p_actor_id
      and staff_roles.role = 'admin'
      and staff_roles.status = 'active'
  ) then
    raise exception 'Actor is not an active administrator';
  end if;
  if p_role not in ('admin', 'moderator', 'help_editor', 'content_editor')
    or p_status not in ('active', 'suspended') then
    raise exception 'Invalid staff role request';
  end if;

  select users.id into target_user_id
  from auth.users as users
  where lower(users.email) = lower(trim(p_email))
  limit 1;
  if target_user_id is null then
    raise exception 'Target account not found';
  end if;

  perform 1
  from public.staff_roles as roles
  where roles.role = 'admin' and roles.status = 'active'
  order by roles.user_id
  for update;

  if p_role = 'admin' and p_status = 'suspended' and exists (
    select 1 from public.staff_roles as roles
    where roles.user_id = target_user_id
      and roles.role = 'admin'
      and roles.status = 'active'
  ) then
    select count(*) into active_admins
    from public.staff_roles as roles
    where roles.role = 'admin' and roles.status = 'active';
    if active_admins <= 1 then
      raise exception 'Cannot suspend the last active administrator';
    end if;
  end if;

  insert into public.staff_roles (user_id, role, status, last_edited_by, updated_at)
  values (target_user_id, p_role, p_status, p_actor_id, now())
  on conflict (user_id, role) do update
    set status = excluded.status,
        last_edited_by = excluded.last_edited_by,
        updated_at = excluded.updated_at;

  return query
    select roles.user_id, users.email::text, roles.role, roles.status, roles.updated_at
    from public.staff_roles as roles
    join auth.users as users on users.id = roles.user_id
    where roles.user_id = target_user_id and roles.role = p_role;
end;
$$;

revoke all on function public.manage_staff_role(uuid, text, text, text)
  from public, anon, authenticated;
grant execute on function public.manage_staff_role(uuid, text, text, text)
  to service_role;

create or replace function public.audit_community_moderation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.status is distinct from old.status
    and new.moderated_by is not null
    and new.status in ('published', 'hidden', 'rejected') then
    insert into public.staff_audit_events (actor_id, action, target_type, target_id)
    values (new.moderated_by, 'community.' || new.status, 'community_post', new.id);
  end if;
  return new;
end;
$$;

drop trigger if exists anonymous_posts_audit_trigger on public.anonymous_posts;
create trigger anonymous_posts_audit_trigger
after update of status on public.anonymous_posts
for each row execute function public.audit_community_moderation();

revoke all on function public.audit_community_moderation()
  from public, anon, authenticated;

create or replace function public.audit_help_resource_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  event_action text;
begin
  if new.last_edited_by is null then
    return new;
  end if;

  if tg_op = 'INSERT' then
    event_action := 'help.created';
  elsif new.verification_status is distinct from old.verification_status then
    event_action := case new.verification_status
      when 'verified' then 'help.verified'
      when 'retired' then 'help.retired'
      when 'stale' then 'help.stale'
      else 'help.updated'
    end;
  elsif new.updated_at is distinct from old.updated_at then
    event_action := 'help.updated';
  end if;

  if event_action is not null then
    insert into public.staff_audit_events (actor_id, action, target_type, target_id)
    values (new.last_edited_by, event_action, 'help_resource', new.id);
  end if;
  return new;
end;
$$;

drop trigger if exists help_resources_audit_trigger on public.help_resources;
create trigger help_resources_audit_trigger
after insert or update on public.help_resources
for each row execute function public.audit_help_resource_change();

revoke all on function public.audit_help_resource_change()
  from public, anon, authenticated;

create or replace function public.audit_editorial_content_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  event_action text;
begin
  if new.last_edited_by is null then
    return new;
  end if;

  if tg_op = 'INSERT' then
    event_action := 'content.created';
  elsif new.status is distinct from old.status then
    event_action := case new.status
      when 'published' then 'content.published'
      when 'retired' then 'content.retired'
      else 'content.updated'
    end;
  elsif new.updated_at is distinct from old.updated_at then
    event_action := 'content.updated';
  end if;

  if event_action is not null then
    insert into public.staff_audit_events (actor_id, action, target_type, target_id)
    values (new.last_edited_by, event_action, 'editorial_content', new.id);
  end if;
  return new;
end;
$$;

drop trigger if exists editorial_content_audit_trigger on public.editorial_content;
create trigger editorial_content_audit_trigger
after insert or update on public.editorial_content
for each row execute function public.audit_editorial_content_change();

revoke all on function public.audit_editorial_content_change()
  from public, anon, authenticated;

create table if not exists public.notification_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  enabled boolean not null default false,
  local_time time not null default '07:00',
  timezone text not null default 'Atlantic/Cape_Verde',
  last_sent_on date,
  delivery_claimed_on date,
  delivery_claimed_at timestamptz,
  updated_at timestamptz not null default now()
);

alter table public.notification_preferences
  add column if not exists last_sent_on date;
alter table public.notification_preferences
  add column if not exists delivery_claimed_on date;
alter table public.notification_preferences
  add column if not exists delivery_claimed_at timestamptz;

create index if not exists notification_preferences_due_idx
  on public.notification_preferences (enabled, local_time)
  where enabled = true;

create or replace function public.claim_push_delivery(
  p_user_id uuid,
  p_local_day date,
  p_claimed_at timestamptz
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  affected integer;
begin
  if p_user_id is null or p_local_day is null or p_claimed_at is null then
    return false;
  end if;

  update public.notification_preferences
    set delivery_claimed_on = p_local_day,
        delivery_claimed_at = p_claimed_at,
        updated_at = p_claimed_at
    where user_id = p_user_id
      and enabled = true
      and last_sent_on is distinct from p_local_day
      and (
        delivery_claimed_on is distinct from p_local_day
        or delivery_claimed_at is null
        or delivery_claimed_at < p_claimed_at - interval '5 minutes'
      );

  get diagnostics affected = row_count;
  return affected = 1;
end;
$$;

create or replace function public.complete_push_delivery(
  p_user_id uuid,
  p_local_day date,
  p_completed_at timestamptz
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  affected integer;
begin
  update public.notification_preferences
    set last_sent_on = p_local_day,
        delivery_claimed_on = null,
        delivery_claimed_at = null,
        updated_at = p_completed_at
    where user_id = p_user_id
      and delivery_claimed_on = p_local_day;

  get diagnostics affected = row_count;
  return affected = 1;
end;
$$;

create or replace function public.release_push_delivery(
  p_user_id uuid,
  p_local_day date,
  p_released_at timestamptz
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  affected integer;
begin
  update public.notification_preferences
    set delivery_claimed_on = null,
        delivery_claimed_at = null,
        updated_at = p_released_at
    where user_id = p_user_id
      and delivery_claimed_on = p_local_day;

  get diagnostics affected = row_count;
  return affected = 1;
end;
$$;

revoke all on function public.claim_push_delivery(uuid, date, timestamptz)
  from public, anon, authenticated;
grant execute on function public.claim_push_delivery(uuid, date, timestamptz)
  to service_role;
revoke all on function public.complete_push_delivery(uuid, date, timestamptz)
  from public, anon, authenticated;
grant execute on function public.complete_push_delivery(uuid, date, timestamptz)
  to service_role;
revoke all on function public.release_push_delivery(uuid, date, timestamptz)
  from public, anon, authenticated;
grant execute on function public.release_push_delivery(uuid, date, timestamptz)
  to service_role;

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

alter table public.push_subscriptions
  drop constraint if exists push_subscriptions_endpoint_safe;
alter table public.push_subscriptions
  add constraint push_subscriptions_endpoint_safe check (
    length(endpoint) between 12 and 2048
    and endpoint ~ '^https://[^[:space:]@/]+'
    and lower(endpoint) !~ '^https://(localhost|[^/]+\.(localhost|local|internal)|127\.|10\.|169\.254\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)'
  ) not valid;
alter table public.push_subscriptions
  drop constraint if exists push_subscriptions_key_material_safe;
alter table public.push_subscriptions
  add constraint push_subscriptions_key_material_safe check (
    length(p256dh) between 16 and 512
    and p256dh ~ '^[A-Za-z0-9_-]+={0,2}$'
    and length(auth_secret) between 8 and 256
    and auth_secret ~ '^[A-Za-z0-9_-]+={0,2}$'
    and (user_agent is null or length(user_agent) <= 500)
  ) not valid;

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
alter table public.staff_roles enable row level security;
alter table public.staff_audit_events enable row level security;
alter table public.anonymous_posts enable row level security;
alter table public.anonymous_reports enable row level security;
alter table public.help_resources enable row level security;
alter table public.editorial_content enable row level security;
alter table public.notification_preferences enable row level security;
alter table public.push_subscriptions enable row level security;
alter table public.ai_daily_usage enable row level security;
alter table public.community_daily_usage enable row level security;

-- Browser roles need table privileges before PostgreSQL evaluates RLS. Keep
-- anonymous visitors out and grant authenticated users only the operations
-- covered by the per-user policies below.
revoke all on table public.journey_state from anon, authenticated;
grant select, insert, update, delete on table public.journey_state to authenticated;

revoke all on table public.notification_preferences from anon, authenticated;
grant select, insert, update, delete on table public.notification_preferences to authenticated;

revoke all on table public.push_subscriptions from anon, authenticated;
grant select, insert, update, delete on table public.push_subscriptions to authenticated;

-- New Supabase projects can omit default table grants. The secret API key
-- assumes the service_role database role, but RLS bypass does not replace the
-- underlying SQL privileges required by PostgREST.
grant select, insert, update, delete on table
  public.journey_state,
  public.staff_roles,
  public.staff_audit_events,
  public.anonymous_posts,
  public.anonymous_reports,
  public.help_resources,
  public.editorial_content,
  public.notification_preferences,
  public.push_subscriptions,
  public.ai_daily_usage,
  public.community_daily_usage
to service_role;

-- Supabase may install this event-trigger helper to enable RLS on new tables.
-- Event triggers do not need browser roles to execute the helper directly.
do $$
begin
  if to_regprocedure('public.rls_auto_enable()') is not null then
    revoke all on function public.rls_auto_enable()
      from public, anon, authenticated;
  end if;
end;
$$;

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
drop policy if exists "Users read staff roles" on public.staff_roles;
drop policy if exists "Users read staff audit events" on public.staff_audit_events;

drop policy if exists "Public reads verified help resources" on public.help_resources;
drop policy if exists "Public reads editorial content" on public.editorial_content;

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
