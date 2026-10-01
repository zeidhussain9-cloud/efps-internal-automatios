BEGIN;

CREATE TABLE IF NOT EXISTS public.crm_inventory_sync_changes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id text NOT NULL REFERENCES public.crm_inventory_sync_runs(run_id),
  listing_id text NOT NULL,
  change_type text NOT NULL CHECK (change_type IN ('created','updated','restored','deleted')),
  field_name text,
  old_value jsonb,
  new_value jsonb,
  source_hash_before text,
  source_hash_after text,
  changed_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS crm_inventory_sync_changes_listing_idx
  ON public.crm_inventory_sync_changes (listing_id, changed_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS crm_inventory_sync_changes_run_idx
  ON public.crm_inventory_sync_changes (run_id, id);

ALTER TABLE public.crm_inventory_sync_changes ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.crm_inventory_sync_changes FROM anon, authenticated;
GRANT SELECT, INSERT ON public.crm_inventory_sync_changes TO service_role;

-- Reconcile the 13 historical event rows whose message linkage already proves
-- the current promoted lead relationship.
UPDATE public.crm_webhook_events e
SET lead_id = m.lead_id,
    message_id = COALESCE(e.message_id, m.id)
FROM public.crm_messages m
WHERE e.lead_id IS NULL
  AND m.lead_id IS NOT NULL
  AND m.source_number = e.source_number
  AND m.provider_message_id = e.provider_event_id;

-- Harden recovery for the transient state observed during the live audit:
-- if a personal event already has its durable message, its event state can be
-- finalized atomically from that message linkage instead of waiting for retry.
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
        e.id,e.source_number,e.phone,e.direction,e.message_type,
        body_text,
        COALESCE(e.payload->>'from_name',e.payload->>'contact_name'),
        media_urls,media_filenames,e.message_at
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

COMMIT;
