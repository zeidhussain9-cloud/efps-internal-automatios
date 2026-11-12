-- Group-chat messages are evidence, not a lead's personal conversation timeline.
-- Preserve the prior association in reconciliation_history before unlinking it.
BEGIN;

ALTER TABLE public.crm_webhook_events
  ADD COLUMN IF NOT EXISTS reconciliation_history jsonb NOT NULL DEFAULT '[]'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='public.crm_webhook_events'::regclass
      AND conname='crm_webhook_events_reconciliation_history_check'
  ) THEN
    ALTER TABLE public.crm_webhook_events
      ADD CONSTRAINT crm_webhook_events_reconciliation_history_check
      CHECK (jsonb_typeof(reconciliation_history)='array');
  END IF;
END $$;

WITH target AS MATERIALIZED (
  SELECT id,message_id,lead_id,payload->>'chat_id' AS group_chat_id
  FROM public.crm_webhook_events
  WHERE event_type='messages'
    AND payload->>'chat_id' LIKE '%@g.us'
    AND lead_id IS NOT NULL
),
updated_events AS (
  UPDATE public.crm_webhook_events e
  SET reconciliation_history=e.reconciliation_history || jsonb_build_array(
        jsonb_build_object(
          'action','group_message_unlinked_from_lead',
          'previous_lead_id',t.lead_id,
          'group_chat_id',t.group_chat_id,
          'recorded_at',now()
        )
      ),
      lead_id=NULL
  FROM target t
  WHERE e.id=t.id
  RETURNING e.id,e.message_id
),
updated_messages AS (
  UPDATE public.crm_messages m
  SET lead_id=NULL
  FROM updated_events e
  WHERE m.id=e.message_id AND m.lead_id IS NOT NULL
  RETURNING m.id
)
INSERT INTO public.crm_activity(lead_id,actor,action,details)
SELECT NULL,'webhook-reconciliation','group_messages.unlinked',
  jsonb_build_object(
    'message_count',(SELECT count(*) FROM updated_messages),
    'event_count',(SELECT count(*) FROM updated_events),
    'affected_lead_count',(SELECT count(DISTINCT lead_id) FROM target),
    'affected_group_count',(SELECT count(DISTINCT group_chat_id) FROM target),
    'reason','Group messages must not be attached to a promoted contact lead timeline.'
  );

COMMIT;