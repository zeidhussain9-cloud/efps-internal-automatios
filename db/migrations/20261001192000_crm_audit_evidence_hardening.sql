BEGIN;
CREATE INDEX IF NOT EXISTS crm_requirement_evidence_source_message_idx ON public.crm_requirement_evidence (source_message_id);
CREATE INDEX IF NOT EXISTS crm_webhook_events_message_idx ON public.crm_webhook_events (message_id);
CREATE OR REPLACE FUNCTION public.crm_touch_lead_requirements_updated_at()
RETURNS trigger LANGUAGE plpgsql SET search_path TO '' AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;
DO $$
DECLARE d public.crm_drafts%ROWTYPE;
DECLARE mapped_ids bigint[];
DECLARE original_ids bigint[];
DECLARE repaired_count integer;
DECLARE dropped_count integer;
BEGIN
  FOR d IN SELECT * FROM public.crm_drafts
    WHERE EXISTS (
      SELECT 1
      FROM unnest(evidence_message_ids) WITH ORDINALITY r(ref,ord)
      WHERE NOT EXISTS (SELECT 1 FROM public.crm_messages x WHERE x.id=r.ref::bigint AND x.lead_id=d.lead_id)
    )
  LOOP
    original_ids := d.evidence_message_ids;
    SELECT COALESCE(array_agg(mapped_id ORDER BY ord) FILTER (WHERE mapped_id IS NOT NULL),'{}'::bigint[])
    INTO mapped_ids
    FROM (
      SELECT r.ord,
             CASE
               WHEN EXISTS (SELECT 1 FROM public.crm_messages x WHERE x.id=r.ref::bigint AND x.lead_id=d.lead_id)
                 THEN r.ref::bigint
               ELSE (
                 SELECT m.id FROM public.crm_messages m
                 WHERE m.lead_id=d.lead_id AND m.source_message_id=r.ref::text
                 ORDER BY m.id LIMIT 1
               )
             END AS mapped_id
      FROM unnest(d.evidence_message_ids) WITH ORDINALITY r(ref,ord)
    ) q;

    SELECT count(*) INTO repaired_count
    FROM unnest(original_ids) WITH ORDINALITY r(ref,ord)
    WHERE NOT EXISTS (SELECT 1 FROM public.crm_messages x WHERE x.id=r.ref::bigint AND x.lead_id=d.lead_id)
      AND EXISTS (SELECT 1 FROM public.crm_messages m WHERE m.lead_id=d.lead_id AND m.source_message_id=r.ref::text);

    dropped_count := cardinality(original_ids) - cardinality(mapped_ids) - repaired_count;
    UPDATE public.crm_drafts SET evidence_message_ids=mapped_ids WHERE id=d.id;
    INSERT INTO public.crm_activity(lead_id,actor,action,details)
    VALUES (d.lead_id,'system','ai.evidence.reconciled',
      jsonb_build_object('draft_id',d.id,'repaired_refs',repaired_count,'dropped_unresolved_refs',greatest(dropped_count,0)));
  END LOOP;
END;
$$;
COMMIT;