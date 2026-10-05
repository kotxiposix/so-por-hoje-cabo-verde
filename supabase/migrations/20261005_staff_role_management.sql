-- Admin-managed staff roles. Safe to run more than once.

alter table public.staff_roles
  add column if not exists last_edited_by uuid references auth.users(id) on delete set null;

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
