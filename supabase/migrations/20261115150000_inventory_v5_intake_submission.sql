-- STAGED ONLY. Existing-destination submission ledger; never source completion.
BEGIN;
CREATE TABLE public.inventory_intake_submissions(
 source_page_id uuid PRIMARY KEY,payload_hash text NOT NULL CHECK(payload_hash ~ '^[a-f0-9]{64}$'),
 destination_page_id uuid NOT NULL,listing_id text NOT NULL,candidate jsonb NOT NULL,
 phase text NOT NULL DEFAULT 'claimed' CHECK(phase IN ('claimed','planned','awaiting_source_ack')),
 plan jsonb,lease_token uuid,lease_until timestamptz,updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE public.inventory_intake_submissions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_intake_submissions FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.inventory_intake_submissions TO service_role;
CREATE OR REPLACE FUNCTION public.inventory_v5_intake_submission(p_operation text,
 p_source_page_id uuid,p_payload_hash text DEFAULT NULL,p_destination_page_id uuid DEFAULT NULL,
 p_listing_id text DEFAULT NULL,p_candidate jsonb DEFAULT NULL,p_lease uuid DEFAULT NULL,p_plan jsonb DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_intake_submissions%ROWTYPE;token uuid;w public.inventory_processing_revisions%ROWTYPE;m public.crm_inventory_snapshot%ROWTYPE;
BEGIN
 IF p_operation='claim' THEN
  IF p_payload_hash IS NULL OR p_payload_hash !~ '^[a-f0-9]{64}$' OR p_destination_page_id IS NULL OR
   coalesce(p_listing_id,'') !~ '^EF-[0-9]{4}-[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{4}$' OR
   jsonb_typeof(p_candidate) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Bound submission required'; END IF;
  INSERT INTO public.inventory_intake_submissions(source_page_id,payload_hash,destination_page_id,listing_id,candidate)
   VALUES(p_source_page_id,p_payload_hash,p_destination_page_id,p_listing_id,p_candidate) ON CONFLICT DO NOTHING;
  SELECT * INTO r FROM public.inventory_intake_submissions WHERE source_page_id=p_source_page_id FOR UPDATE;
  IF r.payload_hash IS DISTINCT FROM p_payload_hash OR r.destination_page_id IS DISTINCT FROM p_destination_page_id OR
   r.listing_id IS DISTINCT FROM p_listing_id OR r.candidate IS DISTINCT FROM p_candidate THEN
   RAISE EXCEPTION 'Earlier source submission unresolved or immutable binding changed'; END IF;
  IF r.lease_until>clock_timestamp() THEN RETURN jsonb_build_object('busy',true); END IF;
  token=gen_random_uuid();
  UPDATE public.inventory_intake_submissions SET lease_token=token,lease_until=clock_timestamp()+interval '90 seconds',updated_at=clock_timestamp()
   WHERE source_page_id=p_source_page_id RETURNING * INTO r;
  RETURN to_jsonb(r);
 END IF;
 SELECT * INTO r FROM public.inventory_intake_submissions WHERE source_page_id=p_source_page_id FOR UPDATE;
 IF NOT FOUND OR r.lease_token IS DISTINCT FROM p_lease OR r.lease_until<=clock_timestamp() THEN RAISE EXCEPTION 'Stale source submission lease'; END IF;
 IF p_operation='renew' THEN
  UPDATE public.inventory_intake_submissions SET lease_until=clock_timestamp()+interval '90 seconds' WHERE source_page_id=p_source_page_id;
 ELSIF p_operation='plan' THEN
  IF r.phase<>'claimed' OR jsonb_typeof(p_plan) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Single durable plan required'; END IF;
  UPDATE public.inventory_intake_submissions SET phase='planned',plan=p_plan WHERE source_page_id=p_source_page_id;
 ELSIF p_operation='destination_ack' THEN
  IF r.phase NOT IN ('planned','awaiting_source_ack') THEN RAISE EXCEPTION 'Destination plan not acknowledged'; END IF;
  SELECT * INTO w FROM public.inventory_processing_revisions WHERE page_id=r.destination_page_id FOR UPDATE;
  IF NOT FOUND OR w.listing_id IS DISTINCT FROM r.listing_id OR w.pending_patch IS NOT NULL OR w.active_effect IS NOT NULL OR
   w.revision IS DISTINCT FROM (r.plan->>'revision')::bigint+1 OR
   w.last_acknowledged_values-'_edited_at' IS DISTINCT FROM ((r.plan->'before')||(r.plan->'patch'))-'_edited_at' THEN RAISE EXCEPTION 'Destination row not exactly acknowledged'; END IF;
  SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=r.listing_id;
  IF NOT FOUND OR m.deleted_at IS NOT NULL OR m.inventory_contract_version IS DISTINCT FROM 5 OR
   m.inventory_revision IS DISTINCT FROM (r.plan->>'revision')::bigint OR
   m.source_record->>'notion_page_id' IS DISTINCT FROM r.destination_page_id::text OR
   NOT(m.source_record @> (w.last_acknowledged_values-'_edited_at'-'_archived')) THEN RAISE EXCEPTION 'Destination mirror not exactly acknowledged'; END IF;
  UPDATE public.inventory_intake_submissions SET phase='awaiting_source_ack' WHERE source_page_id=p_source_page_id;
 ELSIF p_operation='release' THEN
  UPDATE public.inventory_intake_submissions SET lease_token=NULL,lease_until=NULL WHERE source_page_id=p_source_page_id;
 ELSE RAISE EXCEPTION 'Unsupported submission operation; source completion not implemented'; END IF;
 RETURN jsonb_build_object('ok',true,'source_completion_allowed',false);
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_intake_submission FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_intake_submission TO service_role;
COMMIT;
