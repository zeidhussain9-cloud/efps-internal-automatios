-- Reconcile any webhook events that were durably recorded but not yet completed.
-- Safe to run repeatedly: crm_process_webhook_event is idempotent at the message layer.
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT *
    FROM public.crm_webhook_events
    WHERE processing_status = 'received'
    ORDER BY id
  LOOP
    PERFORM public.crm_process_webhook_event(
      r.id,
      r.source_number,
      r.phone,
      r.direction,
      r.message_type,
      CASE
        WHEN jsonb_typeof(r.payload->'text') = 'object'
        THEN r.payload->'text'->>'body'
        ELSE NULL
      END,
      COALESCE(r.payload->>'from_name', r.payload->>'contact_name'),
      NULL,
      NULL,
      r.message_at
    );
  END LOOP;
END $$;
