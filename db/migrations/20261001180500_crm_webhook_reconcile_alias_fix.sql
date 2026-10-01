-- Hotfix for the production reconciler hardening migration.
CREATE OR REPLACE FUNCTION public.crm_reconcile_received_webhooks()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $$
DECLARE
  e public.crm_webhook_events%ROWTYPE;
  processed_count integer := 0;
  body_text text;
  media_urls jsonb;
  media_filenames jsonb;
BEGIN
  UPDATE public.crm_webhook_events AS we
  SET processing_status='processed',
      lead_id=m.lead_id,
      message_id=m.id,
      processed_at=COALESCE(we.processed_at,now()),
      processing_error=NULL
  FROM public.crm_messages AS m
  WHERE we.processing_status IN ('received','processing')
    AND we.phone IS NOT NULL
    AND m.source_number=we.source_number
    AND m.provider_message_id=we.provider_event_id
    AND m.id IS NOT NULL;

  FOR e IN SELECT * FROM public.crm_webhook_events
    WHERE processing_status='received'
      AND source_number IN ('+919148338801','+917975102130','+919902024973')
    ORDER BY id FOR UPDATE SKIP LOCKED
  LOOP
    body_text := CASE WHEN jsonb_typeof(e.payload->'text')='object'
      THEN NULLIF(btrim(e.payload->'text'->>'body'),'') ELSE NULL END;
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
$$;

REVOKE ALL ON FUNCTION public.crm_reconcile_received_webhooks() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.crm_reconcile_received_webhooks() TO postgres;
