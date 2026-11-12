-- Backfill all historical message events that were previously marked processed without a crm_messages link.
-- Process in bounded batches so the existing one-minute cron can safely continue recovery.
BEGIN;

CREATE OR REPLACE FUNCTION public.crm_reconcile_received_webhooks()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $function$
DECLARE
  e public.crm_webhook_events%ROWTYPE;
  processed_count integer := 0;
  body_text text;
BEGIN
  -- First attach any already-persisted messages, including messages without a contact phone.
  UPDATE public.crm_webhook_events AS we
  SET processing_status='processed',lead_id=m.lead_id,message_id=m.id,
      processed_at=COALESCE(we.processed_at,now()),
      processing_error_history=CASE WHEN we.processing_error IS NULL THEN we.processing_error_history
        ELSE we.processing_error_history || jsonb_build_array(jsonb_build_object('error',we.processing_error,'recorded_at',now(),'reconciled_at',now())) END,
      processing_error=NULL
  FROM public.crm_messages AS m
  WHERE we.event_type='messages'
    AND we.processing_status IN ('received','processing','processed')
    AND we.message_id IS NULL
    AND m.source_number=we.source_number
    AND ((we.provider_event_id IS NOT NULL AND m.provider_message_id=we.provider_event_id)
      OR (we.provider_event_id IS NULL AND m.source_message_id='whapi-event-row:'||we.id::text));

  FOR e IN
    SELECT * FROM public.crm_webhook_events
    WHERE source_number IN ('+919148338801','+917975102130','+919902024973')
      AND event_type='messages'
      AND (processing_status IN ('received','processing')
        OR (processing_status='processed' AND message_id IS NULL))
    ORDER BY id LIMIT 500 FOR UPDATE SKIP LOCKED
  LOOP
    body_text := COALESCE(
      CASE WHEN jsonb_typeof(e.payload->'text')='object'
        THEN NULLIF(btrim(e.payload->'text'->>'body'),'') ELSE NULL END,
      CASE WHEN jsonb_typeof(e.payload->'link_preview')='object'
        THEN NULLIF(btrim(e.payload->'link_preview'->>'body'),'') ELSE NULL END,
      NULLIF(btrim(e.payload->>'body'),'')
    );
    BEGIN
      PERFORM public.crm_process_webhook_event(
        e.id,e.source_number,e.phone,e.direction,e.message_type,
        body_text,COALESCE(e.payload->>'from_name',e.payload->>'contact_name'),
        NULL,NULL,e.message_at
      );
      processed_count := processed_count + 1;
    EXCEPTION WHEN OTHERS THEN
      UPDATE public.crm_webhook_events SET processing_error=left(SQLERRM,1000) WHERE id=e.id;
    END;
  END LOOP;
  RETURN processed_count;
END;
$function$;


REVOKE ALL ON FUNCTION public.crm_reconcile_received_webhooks() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.crm_reconcile_received_webhooks() TO postgres;

COMMIT;