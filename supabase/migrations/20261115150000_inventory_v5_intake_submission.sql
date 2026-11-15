-- STAGED ONLY. Existing-destination submission ledger; never source completion.
BEGIN;
CREATE TABLE public.inventory_intake_submissions(
 source_page_id uuid PRIMARY KEY,payload_hash text NOT NULL CHECK(payload_hash ~ '^[a-f0-9]{64}$'),
 destination_page_id uuid NOT NULL,listing_id text NOT NULL,candidate jsonb NOT NULL,
 phase text NOT NULL DEFAULT 'claimed' CHECK(phase IN ('claimed','planned','awaiting_source_ack')),
 plan jsonb,source_ack_plan jsonb,lease_token uuid,lease_until timestamptz,updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
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
 IF p_operation='claim_existing' THEN
  SELECT * INTO r FROM public.inventory_intake_submissions WHERE source_page_id=p_source_page_id FOR UPDATE;
  IF NOT FOUND THEN RETURN jsonb_build_object('found',false); END IF;
  IF r.lease_until>clock_timestamp() THEN RETURN jsonb_build_object('found',true,'busy',true); END IF;
  token=gen_random_uuid();
  UPDATE public.inventory_intake_submissions SET lease_token=token,lease_until=clock_timestamp()+interval '90 seconds'
   WHERE source_page_id=p_source_page_id RETURNING * INTO r;
  RETURN to_jsonb(r)||jsonb_build_object('found',true);
 END IF;
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
 ELSIF p_operation='prepare_source_ack' THEN
  IF r.phase<>'awaiting_source_ack' OR jsonb_typeof(p_plan) IS DISTINCT FROM 'object' OR
   p_plan->>'payload_hash' IS DISTINCT FROM r.payload_hash OR p_plan->>'listing_id' IS DISTINCT FROM r.listing_id OR
   p_plan->>'destination_page_id' IS DISTINCT FROM r.destination_page_id::text OR
   (p_plan->>'destination_revision')::bigint IS DISTINCT FROM (r.plan->>'revision')::bigint+1 OR
   p_plan->>'source_completion_allowed' IS DISTINCT FROM 'false' OR p_plan->>'source_status_unresolved' IS DISTINCT FROM 'true' OR
   p_plan->'properties' IS DISTINCT FROM jsonb_build_object('Listing ID',jsonb_build_object('rich_text',jsonb_build_array(jsonb_build_object('type','text','text',jsonb_build_object('content',r.listing_id)))),
    'Processed Property',jsonb_build_object('relation',jsonb_build_array(jsonb_build_object('id',r.destination_page_id::text)))) OR
   coalesce(p_plan->>'source_before_hash','') !~ '^[a-f0-9]{64}$' THEN RAISE EXCEPTION 'Exact source ack preparation required'; END IF;
  SELECT * INTO w FROM public.inventory_processing_revisions WHERE page_id=r.destination_page_id FOR UPDATE;
  SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=r.listing_id FOR UPDATE;
  IF w.listing_id IS DISTINCT FROM r.listing_id OR w.pending_patch IS NOT NULL OR w.active_effect IS NOT NULL OR
   w.revision IS DISTINCT FROM (r.plan->>'revision')::bigint+1 OR
   w.last_acknowledged_values-'_edited_at' IS DISTINCT FROM ((r.plan->'before')||(r.plan->'patch'))-'_edited_at' OR
   m.inventory_revision IS DISTINCT FROM (r.plan->>'revision')::bigint OR m.deleted_at IS NOT NULL OR
   m.source_record->>'notion_page_id' IS DISTINCT FROM r.destination_page_id::text OR
   NOT(m.source_record @> (w.last_acknowledged_values-'_edited_at'-'_archived')) THEN RAISE EXCEPTION 'Destination changed before source ack preparation'; END IF;
  IF r.source_ack_plan IS NOT NULL AND r.source_ack_plan IS DISTINCT FROM p_plan THEN RAISE EXCEPTION 'Source ack plan immutable; source changed'; END IF;
  UPDATE public.inventory_intake_submissions SET source_ack_plan=p_plan WHERE source_page_id=p_source_page_id;
 ELSIF p_operation='release' THEN
  UPDATE public.inventory_intake_submissions SET lease_token=NULL,lease_until=NULL WHERE source_page_id=p_source_page_id;
 ELSE RAISE EXCEPTION 'Unsupported submission operation; source completion not implemented'; END IF;
 RETURN jsonb_build_object('ok',true,'source_completion_allowed',false);
END $$;
CREATE OR REPLACE FUNCTION public.inventory_v5_intake_binding(p_source_page_id uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE e jsonb;s public.inventory_intake_submissions%ROWTYPE;m public.crm_inventory_snapshot%ROWTYPE;
BEGIN
 SELECT * INTO s FROM public.inventory_intake_submissions WHERE source_page_id=p_source_page_id;
 IF FOUND THEN
  e=jsonb_build_object('listing_id',s.listing_id,'listing_page_id',s.destination_page_id,'payload_hash',s.payload_hash);
 ELSE
  SELECT to_jsonb(x) INTO e FROM public.crm_inventory_intake_events x WHERE x.source_page_id=p_source_page_id::text;
 END IF;
 IF e IS NULL OR coalesce(e->>'listing_page_id','')='' THEN RETURN jsonb_build_object('found',false); END IF;
 SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=e->>'listing_id';
 IF NOT FOUND OR m.deleted_at IS NOT NULL OR m.inventory_contract_version IS DISTINCT FROM 5 OR
  m.source_record->>'notion_page_id' IS DISTINCT FROM e->>'listing_page_id' THEN RETURN jsonb_build_object('found',false); END IF;
 RETURN jsonb_build_object('found',true,'source_page_id',p_source_page_id,'listing_id',e->>'listing_id',
  'page_id',e->>'listing_page_id','payload_hash',e->>'payload_hash','active',true);
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_intake_binding FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_intake_binding TO service_role;
CREATE OR REPLACE FUNCTION public.inventory_v5_quarantine_intake(p_page_id uuid,p_listing_id text,p_lease uuid,p_revision bigint)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_processing_revisions%ROWTYPE;m public.crm_inventory_snapshot%ROWTYPE;n bigint;
BEGIN
 SELECT * INTO r FROM public.inventory_processing_revisions WHERE page_id=p_page_id FOR UPDATE;
 IF NOT FOUND OR r.listing_id IS DISTINCT FROM p_listing_id OR r.lease_token IS DISTINCT FROM p_lease OR
  r.lease_until<=clock_timestamp() OR r.revision IS DISTINCT FROM p_revision OR r.pending_kind IS DISTINCT FROM 'intake' THEN
  RAISE EXCEPTION 'Exact active intake lease/revision/binding required for quarantine'; END IF;
 SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=p_listing_id FOR UPDATE;
 IF NOT FOUND OR m.inventory_contract_version IS DISTINCT FROM 5 OR m.source_record->>'notion_page_id' IS DISTINCT FROM p_page_id::text THEN
  RAISE EXCEPTION 'Exact known v5 mirror binding required for intake quarantine'; END IF;
 -- Increment only the mirror revision. Keep the pending row revision/intent
 -- unchanged so recognized replay stays possible; same-revision normal mirror
 -- writes now fail closed until explicit conflict resolution.
 n=greatest(coalesce(m.inventory_revision,0),r.revision)+1;
 UPDATE public.crm_inventory_snapshot SET pipeline_status='Needs Review',business_status='Needs Review',
  source_record=source_record||jsonb_build_object('Pipeline Status','Needs Review','intake_conflict_quarantined',true),
  inventory_revision=n,last_synced_at=clock_timestamp() WHERE listing_id=p_listing_id;
 UPDATE public.inventory_processing_revisions SET processing_status='needs_review' WHERE page_id=p_page_id;
 RETURN jsonb_build_object('ok',true,'quarantined',true,'mirror_revision',n);
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_quarantine_intake FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_quarantine_intake TO service_role;
REVOKE ALL ON FUNCTION public.inventory_v5_intake_submission FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_intake_submission TO service_role;
COMMIT;
