create table if not exists public.crm_inventory_intake_events (
  source_page_id text primary key,
  payload_hash text not null,
  processing_status text not null check (processing_status in ('processing','processed','needs_review','failed')),
  listing_id text,
  listing_page_id text,
  processing_notes text not null default '',
  first_seen_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  processed_at timestamptz
);

create index if not exists crm_inventory_intake_events_updated_at_idx
  on public.crm_inventory_intake_events (updated_at desc);

alter table public.crm_inventory_intake_events enable row level security;
revoke all on table public.crm_inventory_intake_events from anon, authenticated;
grant all on table public.crm_inventory_intake_events to service_role;

create or replace function public.crm_claim_notion_inventory_intake(
  p_source_page_id text,
  p_payload_hash text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_row public.crm_inventory_intake_events%rowtype;
begin
  insert into public.crm_inventory_intake_events(source_page_id,payload_hash,processing_status)
  values (p_source_page_id,p_payload_hash,'processing')
  on conflict (source_page_id) do nothing
  returning * into v_row;

  if found then
    return jsonb_build_object('status','claimed','item',to_jsonb(v_row));
  end if;

  select * into v_row
  from public.crm_inventory_intake_events
  where source_page_id=p_source_page_id
  for update;

  if v_row.processing_status='processed' and v_row.payload_hash=p_payload_hash then
    return jsonb_build_object('status','duplicate','item',to_jsonb(v_row));
  end if;

  if v_row.processing_status='processing' and v_row.updated_at > now()-interval '5 minutes' then
    return jsonb_build_object('status','in_progress','item',to_jsonb(v_row));
  end if;

  update public.crm_inventory_intake_events
  set payload_hash=p_payload_hash, processing_status='processing', updated_at=now(), processed_at=null
  where source_page_id=p_source_page_id
  returning * into v_row;

  return jsonb_build_object('status','claimed','item',to_jsonb(v_row));
end;
$$;

create or replace function public.crm_set_notion_inventory_listing_id(
  p_source_page_id text,
  p_listing_id text
) returns void
language sql
security definer
set search_path = public, pg_temp
as $$
  update public.crm_inventory_intake_events
  set listing_id=p_listing_id, updated_at=now()
  where source_page_id=p_source_page_id;
$$;

create or replace function public.crm_finish_notion_inventory_intake(
  p_source_page_id text,
  p_processing_status text,
  p_listing_page_id text default '',
  p_processing_notes text default ''
) returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if p_processing_status not in ('processed','needs_review','failed') then
    raise exception 'invalid Notion inventory processing status';
  end if;
  update public.crm_inventory_intake_events
  set processing_status=p_processing_status,
      listing_page_id=nullif(p_listing_page_id,''),
      processing_notes=left(coalesce(p_processing_notes,''),1800),
      updated_at=now(),
      processed_at=case when p_processing_status='processed' then now() else null end
  where source_page_id=p_source_page_id;
end;
$$;

revoke all on function public.crm_claim_notion_inventory_intake(text,text) from public, anon, authenticated;
revoke all on function public.crm_set_notion_inventory_listing_id(text,text) from public, anon, authenticated;
revoke all on function public.crm_finish_notion_inventory_intake(text,text,text,text) from public, anon, authenticated;
grant execute on function public.crm_claim_notion_inventory_intake(text,text) to service_role;
grant execute on function public.crm_set_notion_inventory_listing_id(text,text) to service_role;
grant execute on function public.crm_finish_notion_inventory_intake(text,text,text,text) to service_role;
