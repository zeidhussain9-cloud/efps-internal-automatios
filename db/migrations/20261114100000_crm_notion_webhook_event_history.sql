begin;

-- Extend the existing Notion inventory intake ledger. Do not create a parallel
-- webhook table or write Notion events into the WhatsApp message ledger.
alter table public.crm_inventory_intake_events
  add column if not exists event_key text,
  add column if not exists notion_event_id uuid,
  add column if not exists event_type text,
  add column if not exists event_page_id uuid,
  add column if not exists event_payload jsonb,
  add column if not exists payload_sha256 text,
  add column if not exists attempt_number integer,
  add column if not exists delivery_count integer not null default 0,
  add column if not exists delivery_attempts jsonb not null default '[]'::jsonb,
  add column if not exists processing_attempts integer not null default 0,
  add column if not exists processing_error_history jsonb not null default '[]'::jsonb,
  add column if not exists status_history jsonb not null default '[]'::jsonb,
  add column if not exists processing_outcome jsonb,
  add column if not exists aws_request_id text,
  add column if not exists validation_status text;

alter table public.crm_inventory_intake_events
  add constraint crm_inventory_intake_events_event_history_check
    check (event_key is null or (event_key <> '' and length(event_key) <= 220)),
  add constraint crm_inventory_intake_events_event_attempt_check
    check (attempt_number is null or attempt_number between 1 and 8),
  add constraint crm_inventory_intake_events_delivery_count_check
    check (delivery_count >= 0),
  add constraint crm_inventory_intake_events_delivery_attempts_check
    check (jsonb_typeof(delivery_attempts) = 'array'),
  add constraint crm_inventory_intake_events_processing_attempts_check
    check (processing_attempts >= 0),
  add constraint crm_inventory_intake_events_error_history_check
    check (jsonb_typeof(processing_error_history) = 'array'),
  add constraint crm_inventory_intake_events_status_history_check
    check (jsonb_typeof(status_history) = 'array');

create unique index if not exists crm_inventory_intake_events_event_key_idx
  on public.crm_inventory_intake_events (event_key) where event_key is not null;
create index if not exists crm_inventory_intake_events_event_page_idx
  on public.crm_inventory_intake_events (event_page_id, updated_at desc) where event_page_id is not null;

create or replace function public.crm_record_notion_webhook_event(
  p_event_key text,
  p_notion_event_id uuid,
  p_event_type text,
  p_page_id uuid,
  p_event_timestamp timestamptz,
  p_attempt_number integer,
  p_payload jsonb,
  p_payload_sha256 text
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_row public.crm_inventory_intake_events%rowtype;
  v_should_enqueue boolean := false;
  v_previous_attempt integer;
  v_event_source_key text := 'notion-webhook:' || p_event_key;
  v_attempt jsonb;
begin
  if p_event_key is null or length(p_event_key) = 0 or length(p_event_key) > 200 then
    raise exception 'invalid Notion event key';
  end if;
  if p_payload_sha256 is null or p_payload_sha256 !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid Notion payload fingerprint';
  end if;
  if p_attempt_number is not null and p_attempt_number not between 1 and 8 then
    raise exception 'invalid Notion delivery attempt';
  end if;
  v_attempt := jsonb_build_object('attempt_number',p_attempt_number,'received_at',now(),'payload_sha256',p_payload_sha256);

  insert into public.crm_inventory_intake_events (
    source_page_id,payload_hash,processing_status,event_key,notion_event_id,event_type,
    event_page_id,event_payload,payload_sha256,attempt_number,delivery_count,
    delivery_attempts,processing_attempts,status_history
  ) values (
    v_event_source_key,p_payload_sha256,'processing',p_event_key,p_notion_event_id,
    coalesce(nullif(p_event_type,''),'unknown'),p_page_id,coalesce(p_payload,'{}'::jsonb),
    p_payload_sha256,p_attempt_number,1,jsonb_build_array(v_attempt),0,
    jsonb_build_array(jsonb_build_object('status','received','at',now()),jsonb_build_object('status','accepted','at',now()))
  ) on conflict (source_page_id) do nothing returning * into v_row;

  if found then
    return jsonb_build_object('id',v_row.source_page_id,'status','accepted','duplicate',false,'should_enqueue',true);
  end if;

  select * into v_row from public.crm_inventory_intake_events where source_page_id=v_event_source_key for update;
  if not found then raise exception 'Notion event receipt conflict could not be resolved'; end if;
  v_previous_attempt := v_row.attempt_number;
  update public.crm_inventory_intake_events
  set delivery_count=delivery_count+1,
      attempt_number=case when p_attempt_number is null then attempt_number else greatest(coalesce(attempt_number,p_attempt_number),p_attempt_number) end,
      delivery_attempts=delivery_attempts || jsonb_build_array(v_attempt),
      updated_at=now()
  where source_page_id=v_event_source_key returning * into v_row;

  v_should_enqueue := v_row.processing_status='failed'
    and p_attempt_number is not null and p_attempt_number > coalesce(v_previous_attempt,0);
  if v_should_enqueue then
    update public.crm_inventory_intake_events
    set processing_status='processing',processing_notes='',processed_at=null,
        status_history=status_history || jsonb_build_array(jsonb_build_object('status','accepted','at',now(),'retry',true,'attempt_number',p_attempt_number)),
        updated_at=now()
    where source_page_id=v_event_source_key returning * into v_row;
  end if;
  return jsonb_build_object('id',v_row.source_page_id,'status',v_row.processing_status,'duplicate',true,'should_enqueue',v_should_enqueue);
end;
$$;

create or replace function public.crm_update_notion_webhook_event(
  p_event_source_key text,
  p_processing_status text,
  p_aws_request_id text default null,
  p_processing_error text default null,
  p_processing_outcome jsonb default null,
  p_page_id uuid default null,
  p_listing_id text default null,
  p_listing_page_id text default null,
  p_validation_status text default null
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_row public.crm_inventory_intake_events%rowtype;
  v_error text := nullif(left(coalesce(p_processing_error,''),1800),'');
begin
  if p_processing_status not in ('accepted','queued','processing','processed','needs_review','failed','rejected','unsupported','ignored') then
    raise exception 'invalid Notion webhook processing status';
  end if;
  select * into v_row from public.crm_inventory_intake_events where source_page_id=p_event_source_key for update;
  if not found or v_row.event_key is null then raise exception 'Notion webhook event does not exist'; end if;
  if p_processing_status in ('processing','queued','accepted') and v_row.processing_status in ('processed','needs_review') then
    return jsonb_build_object('ok',true,'status',v_row.processing_status,'started',false,'id',v_row.source_page_id);
  end if;
  update public.crm_inventory_intake_events
  set processing_status=case when p_processing_status in ('rejected','unsupported','ignored') then 'failed' when p_processing_status in ('accepted','queued') then 'processing' else p_processing_status end,
      processing_attempts=processing_attempts + case when p_processing_status='processing' then 1 else 0 end,
      processing_notes=case when v_error is not null then v_error else processing_notes end,
      processed_at=case when p_processing_status in ('processed','needs_review','failed','rejected','unsupported','ignored') then now() else null end,
      processing_error_history=case when v_error is not null then processing_error_history || jsonb_build_array(jsonb_build_object('at',now(),'attempt',processing_attempts,'aws_request_id',p_aws_request_id,'error',v_error)) else processing_error_history end,
      status_history=status_history || jsonb_build_array(jsonb_build_object('status',p_validation_status,'processing_status',p_processing_status,'at',now(),'aws_request_id',p_aws_request_id,'error',v_error)),
      processing_outcome=coalesce(p_processing_outcome,processing_outcome),
      aws_request_id=coalesce(nullif(p_aws_request_id,''),aws_request_id),
      event_page_id=coalesce(p_page_id,event_page_id),
      listing_id=coalesce(nullif(p_listing_id,''),listing_id),
      listing_page_id=coalesce(nullif(p_listing_page_id,''),listing_page_id),
      validation_status=coalesce(nullif(p_validation_status,''),case when p_processing_status in ('rejected','unsupported','ignored') then p_processing_status else null end,validation_status),
      updated_at=now()
  where source_page_id=p_event_source_key returning * into v_row;
  return jsonb_build_object('ok',true,'status',v_row.processing_status,'started',p_processing_status in ('accepted','queued','processing'),'id',v_row.source_page_id);
end;
$$;

revoke all on function public.crm_record_notion_webhook_event(text,uuid,text,uuid,timestamptz,integer,jsonb,text) from public,anon,authenticated;
revoke all on function public.crm_update_notion_webhook_event(text,text,text,text,jsonb,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.crm_record_notion_webhook_event(text,uuid,text,uuid,timestamptz,integer,jsonb,text) to service_role;
grant execute on function public.crm_update_notion_webhook_event(text,text,text,text,jsonb,uuid,text,text,text) to service_role;

commit;
