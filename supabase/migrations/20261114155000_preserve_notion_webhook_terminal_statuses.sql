alter table public.crm_inventory_intake_events
  drop constraint if exists crm_inventory_intake_events_processing_status_check;

alter table public.crm_inventory_intake_events
  add constraint crm_inventory_intake_events_processing_status_check
  check (processing_status = any (array['processing','processed','needs_review','failed','ignored','rejected','unsupported']::text[]));

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
)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_row public.crm_inventory_intake_events%rowtype;
  v_error text := nullif(left(coalesce(p_processing_error,''),1800),'');
begin
  if p_processing_status not in ('accepted','queued','processing','processed','needs_review','failed','rejected','unsupported','ignored') then
    raise exception 'invalid Notion webhook processing status';
  end if;
  select * into v_row from public.crm_inventory_intake_events where source_page_id=p_event_source_key for update;
  if not found or v_row.event_key is null then raise exception 'Notion webhook event does not exist'; end if;
  if p_processing_status in ('processing','queued','accepted') and v_row.processing_status in ('processed','needs_review','ignored','rejected','unsupported') then
    return jsonb_build_object('ok',true,'status',v_row.processing_status,'started',false,'id',v_row.source_page_id);
  end if;
  update public.crm_inventory_intake_events
  set processing_status=case when p_processing_status in ('accepted','queued') then 'processing' else p_processing_status end,
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
$function$;

-- Correct the two historical rows after their causes were verified.
update public.crm_inventory_intake_events
set processing_status = 'rejected',
    validation_status = 'rejected',
    processing_notes = 'Unauthenticated empty-body request rejected; no valid Notion event was supplied.',
    processing_outcome = jsonb_build_object('validation','rejected','reason','missing signature or verification token','classification','security_rejection'),
    processed_at = coalesce(processed_at, now()),
    updated_at = now(),
    status_history = status_history || jsonb_build_array(jsonb_build_object('status','rejected','processing_status','rejected','at',now(),'reason','unauthenticated empty-body request'))
where source_page_id = 'notion-webhook:sha256:unverified:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
  and processing_status = 'failed'
  and validation_status = 'rejected';

update public.crm_inventory_intake_events
set processing_status = 'ignored',
    validation_status = 'ignored',
    processing_notes = 'Test-only Codex form smoke-test submission was deleted; this was not a real property intake.',
    processing_outcome = jsonb_build_object('status','ignored','reason','test_only_submission_deleted'),
    processed_at = coalesce(processed_at, now()),
    updated_at = now(),
    status_history = status_history || jsonb_build_array(jsonb_build_object('status','ignored','processing_status','ignored','at',now(),'reason','test-only submission deleted'))
where source_page_id = '417fedf9-b4e8-8199-8c5d-f9e4c2ef7915'
  and processing_status = 'failed';
