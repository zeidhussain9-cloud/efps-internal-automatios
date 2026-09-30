-- Automatic CRM webhook reconciliation.
-- Production invariant: events persisted as "received" are retried automatically.
-- This is a recovery/retry path; the webhook ingress remains the durable first-write boundary.

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
  FOR e IN
    SELECT *
    FROM public.crm_webhook_events
    WHERE processing_status = 'received'
      AND source_number IN ('+919148338801','+917975102130','+919902024973')
    ORDER BY id
    FOR UPDATE SKIP LOCKED
  LOOP
    body_text := CASE
      WHEN jsonb_typeof(e.payload->'text') = 'object'
      THEN NULLIF(btrim(e.payload->'text'->>'body'),'')
      ELSE NULL
    END;

    media_urls := NULL;
    IF jsonb_typeof(e.payload) = 'object' THEN
      media_urls := (
        SELECT jsonb_agg(value)
        FROM jsonb_each(e.payload) AS kv(key,value)
        WHERE key IN ('image','video','document','audio')
          AND jsonb_typeof(value) = 'object'
          AND COALESCE(value->>'link',value->>'url') IS NOT NULL
      );
    END IF;

    BEGIN
      PERFORM public.crm_process_webhook_event(
        e.id,
        e.source_number,
        e.phone,
        e.direction,
        e.message_type,
        body_text,
        COALESCE(e.payload->>'from_name',e.payload->>'contact_name'),
        media_urls,
        media_filenames,
        e.message_at
      );
      processed_count := processed_count + 1;
    EXCEPTION WHEN OTHERS THEN
      UPDATE public.crm_webhook_events
      SET processing_error = left(SQLERRM,1000)
      WHERE id = e.id;
    END;
  END LOOP;

  RETURN processed_count;
END;
$$;

REVOKE ALL ON FUNCTION public.crm_reconcile_received_webhooks() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.crm_reconcile_received_webhooks() TO postgres;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'crm_webhook_reconcile_1m') THEN
    PERFORM cron.unschedule((SELECT jobid FROM cron.job WHERE jobname = 'crm_webhook_reconcile_1m' LIMIT 1));
  END IF;

  PERFORM cron.schedule(
    'crm_webhook_reconcile_1m',
    '* * * * *',
    'select public.crm_reconcile_received_webhooks();'
  );
END $$;
