-- STAGED ONLY. Bound existing-destination/source ledger, not production routing.
BEGIN;
CREATE TABLE public.inventory_intake_submissions(
 source_page_id uuid PRIMARY KEY,payload_hash text NOT NULL CHECK(payload_hash ~ '^[a-f0-9]{64}$'),
 destination_page_id uuid NOT NULL,listing_id text NOT NULL,candidate jsonb NOT NULL,
 phase text NOT NULL DEFAULT 'claimed' CHECK(phase IN ('claimed','planned','awaiting_source_ack','completed')),
 plan jsonb,source_ack_plan jsonb,upstream_outcome jsonb,source_write_plan jsonb,source_effect jsonb,lease_token uuid,lease_until timestamptz,updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE public.inventory_intake_submission_history(
 source_page_id uuid NOT NULL,payload_hash text NOT NULL,record jsonb NOT NULL,
 PRIMARY KEY(source_page_id,payload_hash));
ALTER TABLE public.inventory_intake_submission_history ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_intake_submission_history FROM PUBLIC,anon,authenticated;
CREATE TABLE public.inventory_intake_source_receipts(
 request_id text PRIMARY KEY,source_page_id uuid NOT NULL,effect_id uuid NOT NULL,receipt jsonb NOT NULL);
ALTER TABLE public.inventory_intake_source_receipts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_intake_source_receipts FROM PUBLIC,anon,authenticated;
CREATE TABLE public.inventory_intake_pipeline_runs(
 source_page_id uuid NOT NULL,payload_hash text NOT NULL,destination_page_id uuid NOT NULL,listing_id text NOT NULL,
 token uuid NOT NULL DEFAULT gen_random_uuid(),snapshot jsonb NOT NULL,output jsonb,
 PRIMARY KEY(source_page_id,payload_hash));
ALTER TABLE public.inventory_intake_pipeline_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_intake_pipeline_runs FROM PUBLIC,anon,authenticated;
ALTER TABLE public.inventory_intake_submissions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_intake_submissions FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.inventory_intake_submissions TO service_role;
CREATE OR REPLACE FUNCTION public.inventory_v5_intake_submission(p_operation text,
 p_source_page_id uuid,p_payload_hash text DEFAULT NULL,p_destination_page_id uuid DEFAULT NULL,
 p_listing_id text DEFAULT NULL,p_candidate jsonb DEFAULT NULL,p_lease uuid DEFAULT NULL,p_plan jsonb DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_intake_submissions%ROWTYPE;token uuid;w public.inventory_processing_revisions%ROWTYPE;m public.crm_inventory_snapshot%ROWTYPE;run public.inventory_intake_pipeline_runs%ROWTYPE;b jsonb;
BEGIN
 IF p_operation IN ('begin_pipeline','freeze_pipeline') THEN
  -- Serialize run creation against the source binding, including the first run.
  PERFORM pg_advisory_xact_lock(hashtextextended(p_source_page_id::text,0));
  IF p_operation='begin_pipeline' THEN
   b=public.inventory_v5_intake_binding(p_source_page_id);
   SELECT * INTO r FROM public.inventory_intake_submissions WHERE source_page_id=p_source_page_id FOR UPDATE;
   IF b->>'found' IS DISTINCT FROM 'true' OR b->>'page_id' IS DISTINCT FROM p_destination_page_id::text OR
    b->>'listing_id' IS DISTINCT FROM p_listing_id OR p_payload_hash IS NULL OR p_payload_hash !~ '^[a-f0-9]{64}$' OR
    (r.source_page_id IS NOT NULL AND r.payload_hash<>p_payload_hash AND r.phase<>'completed') OR
    (r.source_page_id IS NULL AND b->>'payload_hash' IS DISTINCT FROM p_payload_hash) OR
    jsonb_typeof(p_plan) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Known bound pipeline version required'; END IF;
   SELECT * INTO run FROM public.inventory_intake_pipeline_runs WHERE source_page_id=p_source_page_id AND payload_hash=p_payload_hash;
   IF FOUND THEN
    IF run.destination_page_id IS DISTINCT FROM p_destination_page_id OR run.listing_id IS DISTINCT FROM p_listing_id OR
     run.snapshot IS DISTINCT FROM p_plan THEN RAISE EXCEPTION 'Pipeline snapshot/binding changed'; END IF;
    RETURN to_jsonb(run)||jsonb_build_object('run_allowed',false,'held',run.output IS NULL);
   END IF;
   INSERT INTO public.inventory_intake_pipeline_runs(source_page_id,payload_hash,destination_page_id,listing_id,snapshot)
    VALUES(p_source_page_id,p_payload_hash,p_destination_page_id,p_listing_id,p_plan) RETURNING * INTO run;
   RETURN to_jsonb(run)||jsonb_build_object('run_allowed',true,'held',false);
  END IF;
  SELECT * INTO run FROM public.inventory_intake_pipeline_runs WHERE source_page_id=p_source_page_id AND payload_hash=p_payload_hash FOR UPDATE;
  IF NOT FOUND OR run.token IS DISTINCT FROM p_lease OR run.output IS NOT NULL OR
   p_plan->'processed'->>'status' IS NULL OR p_plan->'processed'->>'status' NOT IN ('Pending','Needs Review') OR
   p_plan->'processed'->>'listing_id' IS DISTINCT FROM run.listing_id OR jsonb_typeof(p_plan->'issues') IS DISTINCT FROM 'array' THEN
   RAISE EXCEPTION 'Single exact pipeline output required'; END IF;
  UPDATE public.inventory_intake_pipeline_runs SET output=p_plan WHERE source_page_id=p_source_page_id AND payload_hash=p_payload_hash;
  RETURN jsonb_build_object('ok',true,'source_completion_allowed',false);
 END IF;
 IF p_operation IN ('claim_existing','claim_source') THEN
  SELECT * INTO r FROM public.inventory_intake_submissions WHERE source_page_id=p_source_page_id FOR UPDATE;
  IF NOT FOUND THEN RETURN jsonb_build_object('found',false); END IF;
  IF r.source_effect IS NOT NULL AND NOT(p_operation='claim_source' AND r.source_effect ? 'receipt') THEN
   RETURN jsonb_build_object('found',true,'busy',true,'needs_source_effect_review',true); END IF;
  IF r.lease_until>clock_timestamp() THEN RETURN jsonb_build_object('found',true,'busy',true); END IF;
  token=gen_random_uuid();
  UPDATE public.inventory_intake_submissions SET lease_token=token,lease_until=clock_timestamp()+interval '90 seconds'
   WHERE source_page_id=p_source_page_id RETURNING * INTO r;
  IF p_operation='claim_source' AND r.source_effect IS NOT NULL THEN
   UPDATE public.inventory_intake_submissions SET source_effect=source_effect||jsonb_build_object('lease',token)
    WHERE source_page_id=p_source_page_id RETURNING * INTO r;
  END IF;
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
  IF r.source_effect IS NOT NULL THEN RETURN jsonb_build_object('busy',true,'needs_source_effect_review',true); END IF;
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
 ELSIF p_operation='handoff' THEN
  IF r.phase<>'completed' OR r.source_effect->>'status' IS DISTINCT FROM 'committed' OR
   p_payload_hash IS NULL OR p_payload_hash !~ '^[a-f0-9]{64}$' OR p_payload_hash=r.payload_hash OR
   EXISTS(SELECT 1 FROM public.inventory_intake_submission_history WHERE source_page_id=p_source_page_id AND payload_hash=p_payload_hash) OR
   p_destination_page_id IS DISTINCT FROM r.destination_page_id OR p_listing_id IS DISTINCT FROM r.listing_id OR
   jsonb_typeof(p_candidate) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Completed exact previous version required for handoff'; END IF;
  INSERT INTO public.inventory_intake_submission_history VALUES(p_source_page_id,r.payload_hash,to_jsonb(r));
  UPDATE public.inventory_intake_submissions SET payload_hash=p_payload_hash,candidate=p_candidate,phase='claimed',
   plan=NULL,source_ack_plan=NULL,upstream_outcome=NULL,source_write_plan=NULL,source_effect=NULL,
   updated_at=clock_timestamp() WHERE source_page_id=p_source_page_id;
 ELSIF p_operation='quarantine_source_destination' THEN
  SELECT * INTO w FROM public.inventory_processing_revisions WHERE page_id=r.destination_page_id FOR UPDATE;
  SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=r.listing_id FOR UPDATE;
  IF w.lease_token::text IS DISTINCT FROM p_plan->>'row_lease' OR w.lease_until<=clock_timestamp() OR
   w.listing_id IS DISTINCT FROM r.listing_id OR w.revision IS DISTINCT FROM (p_plan->>'revision')::bigint OR
   m.inventory_contract_version IS DISTINCT FROM 5 OR m.source_record->>'notion_page_id' IS DISTINCT FROM r.destination_page_id::text THEN
   RAISE EXCEPTION 'Original acknowledged destination lease/binding required for quarantine'; END IF;
  UPDATE public.crm_inventory_snapshot SET pipeline_status='Needs Review',business_status='Needs Review',
   source_record=source_record||jsonb_build_object('Pipeline Status','Needs Review','source_ack_conflict_quarantined',true),
   inventory_revision=greatest(coalesce(m.inventory_revision,0),w.revision)+1,last_synced_at=clock_timestamp()
   WHERE listing_id=r.listing_id;
  UPDATE public.inventory_processing_revisions SET processing_status='needs_review' WHERE page_id=r.destination_page_id;
 ELSIF p_operation='source_commit' THEN
  IF r.phase<>'awaiting_source_ack' OR r.source_effect->>'status' IS DISTINCT FROM 'finish_prepared' OR
   r.source_effect->'receipt' IS NULL OR r.source_effect->'readback' IS DISTINCT FROM r.source_write_plan->'expected_after' OR
   p_plan->>'effect_id' IS DISTINCT FROM r.source_effect->>'effect_id' OR
   p_plan->'readback' IS DISTINCT FROM r.source_write_plan->'expected_after' THEN RAISE EXCEPTION 'Exact evidenced source finish required'; END IF;
  SELECT * INTO w FROM public.inventory_processing_revisions WHERE page_id=r.destination_page_id FOR UPDATE;
  SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=r.listing_id FOR UPDATE;
  IF w.lease_token::text IS DISTINCT FROM p_plan->>'row_lease' OR w.lease_until<=clock_timestamp() OR
   w.revision IS DISTINCT FROM (r.plan->>'revision')::bigint+1 OR w.pending_patch IS NOT NULL OR w.active_effect IS NOT NULL OR
   w.listing_id IS DISTINCT FROM r.listing_id OR w.last_acknowledged_values-'_edited_at' IS DISTINCT FROM ((r.plan->'before')||(r.plan->'patch'))-'_edited_at' OR
   m.inventory_revision IS DISTINCT FROM (r.plan->>'revision')::bigint OR m.deleted_at IS NOT NULL OR
   m.inventory_contract_version IS DISTINCT FROM 5 OR m.source_record->>'notion_page_id' IS DISTINCT FROM r.destination_page_id::text OR
   NOT(m.source_record @> (w.last_acknowledged_values-'_edited_at'-'_archived')) THEN RAISE EXCEPTION 'Destination changed before final source commit'; END IF;
  UPDATE public.inventory_intake_submissions SET phase='completed',source_effect=source_effect||jsonb_build_object('status','committed') WHERE source_page_id=p_source_page_id;
  RETURN jsonb_build_object('ok',true,'source_completion_allowed',true,'status',r.source_write_plan->>'status');
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
 ELSIF p_operation='capture_outcome' THEN
  IF jsonb_typeof(p_plan) IS DISTINCT FROM 'object' OR p_plan->>'payload_hash' IS DISTINCT FROM r.payload_hash OR
   p_plan->'candidate' IS DISTINCT FROM r.candidate OR p_plan->>'boundary' IS DISTINCT FROM 'existing_pipeline_final_output' OR
   p_plan->'processed'->>'status' NOT IN ('Pending','Needs Review') OR p_plan->'processed'->>'status' IS NULL OR
   jsonb_typeof(p_plan->'issues') IS DISTINCT FROM 'array' OR p_plan->>'source_completion_allowed' IS DISTINCT FROM 'false' OR
   coalesce(p_plan->>'output_hash','') !~ '^[a-f0-9]{64}$' THEN RAISE EXCEPTION 'Exact upstream output required'; END IF;
  IF r.upstream_outcome IS NOT NULL AND r.upstream_outcome IS DISTINCT FROM p_plan THEN RAISE EXCEPTION 'Upstream output immutable'; END IF;
  UPDATE public.inventory_intake_submissions SET upstream_outcome=p_plan WHERE source_page_id=p_source_page_id;
 ELSIF p_operation='prepare_source_write' THEN
  IF r.phase<>'awaiting_source_ack' OR r.upstream_outcome IS NULL OR
   p_plan->>'payload_hash' IS DISTINCT FROM r.payload_hash OR p_plan->>'output_hash' IS DISTINCT FROM r.upstream_outcome->>'output_hash' OR
   p_plan->>'listing_id' IS DISTINCT FROM r.listing_id OR p_plan->>'destination_page_id' IS DISTINCT FROM r.destination_page_id::text OR
   (p_plan->>'destination_revision')::bigint IS DISTINCT FROM (r.plan->>'revision')::bigint+1 OR
   p_plan->>'status' IS DISTINCT FROM (CASE WHEN r.upstream_outcome->'processed'->>'status'='Needs Review' OR jsonb_array_length(r.plan->'conflicts')>0 THEN 'Needs Review' ELSE 'Processed' END) OR
   p_plan->'properties'->'Intake Status'->'status'->>'name' IS DISTINCT FROM p_plan->>'status' OR
   p_plan->'properties'->'Processed Property' IS DISTINCT FROM jsonb_build_object('relation',jsonb_build_array(jsonb_build_object('id',r.destination_page_id::text))) OR
   p_plan->>'source_completion_allowed' IS DISTINCT FROM 'false' OR p_plan->>'effect_required' IS DISTINCT FROM 'true' OR
   coalesce(p_plan->>'source_schema_hash','') !~ '^[a-f0-9]{64}$' OR coalesce(p_plan->>'body_hash','') !~ '^[a-f0-9]{64}$' OR
   p_plan->'properties'->'Listing ID' IS DISTINCT FROM jsonb_build_object('rich_text',jsonb_build_array(jsonb_build_object('type','text','text',jsonb_build_object('content',r.listing_id)))) OR
   (SELECT array_agg(key ORDER BY key) FROM jsonb_each(p_plan->'properties')) IS DISTINCT FROM ARRAY['Intake Status','Listing ID','Processed At','Processed Property','Processing Notes'] THEN RAISE EXCEPTION 'Sealed exact source write preparation required'; END IF;
  SELECT * INTO w FROM public.inventory_processing_revisions WHERE page_id=r.destination_page_id FOR UPDATE;
  SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=r.listing_id FOR UPDATE;
  IF w.revision IS DISTINCT FROM (r.plan->>'revision')::bigint+1 OR w.pending_patch IS NOT NULL OR w.active_effect IS NOT NULL OR
   w.listing_id IS DISTINCT FROM r.listing_id OR w.last_acknowledged_values-'_edited_at' IS DISTINCT FROM ((r.plan->'before')||(r.plan->'patch'))-'_edited_at' OR
   m.inventory_revision IS DISTINCT FROM (r.plan->>'revision')::bigint OR m.deleted_at IS NOT NULL OR m.source_record->>'notion_page_id' IS DISTINCT FROM r.destination_page_id::text OR
   NOT(m.source_record @> (w.last_acknowledged_values-'_edited_at'-'_archived')) THEN RAISE EXCEPTION 'Destination changed before source write'; END IF;
  IF r.source_write_plan IS NOT NULL AND r.source_write_plan IS DISTINCT FROM p_plan THEN RAISE EXCEPTION 'Source write plan immutable'; END IF;
  UPDATE public.inventory_intake_submissions SET source_write_plan=p_plan WHERE source_page_id=p_source_page_id;
 ELSIF p_operation='begin_source_effect' THEN
  IF r.phase<>'awaiting_source_ack' OR r.source_write_plan IS NULL OR r.source_effect IS NOT NULL OR
   p_plan->'source_before' IS DISTINCT FROM r.source_write_plan->'source_before' OR
   p_plan->'source_schema' IS DISTINCT FROM r.source_write_plan->'source_schema' THEN RAISE EXCEPTION 'Exact source snapshot/schema and no unresolved effect required'; END IF;
  SELECT * INTO w FROM public.inventory_processing_revisions WHERE page_id=r.destination_page_id FOR UPDATE;
  SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=r.listing_id FOR UPDATE;
  IF w.revision IS DISTINCT FROM (r.plan->>'revision')::bigint+1 OR w.pending_patch IS NOT NULL OR w.active_effect IS NOT NULL OR
   w.listing_id IS DISTINCT FROM r.listing_id OR w.last_acknowledged_values-'_edited_at' IS DISTINCT FROM ((r.plan->'before')||(r.plan->'patch'))-'_edited_at' OR
   m.inventory_revision IS DISTINCT FROM (r.plan->>'revision')::bigint OR m.deleted_at IS NOT NULL OR m.source_record->>'notion_page_id' IS DISTINCT FROM r.destination_page_id::text OR
   NOT(m.source_record @> (w.last_acknowledged_values-'_edited_at'-'_archived')) THEN RAISE EXCEPTION 'Destination changed before source effect'; END IF;
  token=gen_random_uuid();
  UPDATE public.inventory_intake_submissions SET source_effect=jsonb_build_object('effect_id',token,'lease',p_lease,'intent',r.source_write_plan,'status','begun') WHERE source_page_id=p_source_page_id;
  RETURN jsonb_build_object('effect_id',token,'source_completion_allowed',false);
 ELSIF p_operation IN ('bind_source_dispatch','source_receipt','source_finish_prepare') THEN
  IF r.phase<>'awaiting_source_ack' OR r.source_effect IS NULL OR p_plan->>'effect_id' IS DISTINCT FROM r.source_effect->>'effect_id' OR
    p_plan->>'effect_id' IS NULL OR r.source_effect->>'lease' IS DISTINCT FROM p_lease::text THEN RAISE EXCEPTION 'Source effect nonce/lease mismatch'; END IF;
  IF p_operation='bind_source_dispatch' THEN
   IF r.source_effect ? 'dispatch' OR p_plan->>'method' IS DISTINCT FROM 'PATCH' OR p_plan->>'page_id' IS DISTINCT FROM p_source_page_id::text OR
    p_plan->>'body_hash' IS DISTINCT FROM r.source_write_plan->>'body_hash' THEN RAISE EXCEPTION 'Exact source dispatch required'; END IF;
   UPDATE public.inventory_intake_submissions SET source_effect=source_effect||jsonb_build_object('dispatch',p_plan) WHERE source_page_id=p_source_page_id;
  ELSIF p_operation='source_receipt' THEN
   IF r.source_effect->'dispatch' IS NULL OR r.source_effect ? 'receipt' OR jsonb_typeof(p_plan->'receipt') IS DISTINCT FROM 'object' OR
    coalesce(p_plan->'receipt'->>'status','') !~ '^[0-9]{3}$' OR
    p_plan->'receipt'->'dispatch' IS DISTINCT FROM r.source_effect->'dispatch' OR
    coalesce(p_plan->'receipt'->>'request_id','')='' OR
    NOT coalesce((((p_plan->'receipt'->>'status')::integer BETWEEN 200 AND 299) OR
        (p_plan->'receipt'->>'status'='503' AND p_plan->'receipt'->>'classification'='documented_saved_no_repeat' AND
         p_plan->'receipt'->>'code'='service_unavailable' AND
         p_plan->'receipt'->'additional_data'->'retry_guidance'='["Read the object again to confirm the saved change.","Do not repeat the write."]'::jsonb)),false) THEN RAISE EXCEPTION 'Exact terminal source receipt required'; END IF;
   INSERT INTO public.inventory_intake_source_receipts VALUES(p_plan->'receipt'->>'request_id',p_source_page_id,(p_plan->>'effect_id')::uuid,p_plan->'receipt');
   UPDATE public.inventory_intake_submissions SET source_effect=source_effect||jsonb_build_object('receipt',p_plan->'receipt') WHERE source_page_id=p_source_page_id;
  ELSE
   IF r.source_effect->'receipt' IS NULL OR p_plan->'readback' IS DISTINCT FROM r.source_write_plan->'expected_after' THEN RAISE EXCEPTION 'Exact source readback and terminal receipt required'; END IF;
   SELECT * INTO w FROM public.inventory_processing_revisions WHERE page_id=r.destination_page_id FOR UPDATE;
   SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=r.listing_id FOR UPDATE;
   IF w.revision IS DISTINCT FROM (r.plan->>'revision')::bigint+1 OR w.pending_patch IS NOT NULL OR w.active_effect IS NOT NULL OR
    w.last_acknowledged_values-'_edited_at' IS DISTINCT FROM ((r.plan->'before')||(r.plan->'patch'))-'_edited_at' OR
    m.inventory_revision IS DISTINCT FROM (r.plan->>'revision')::bigint OR m.deleted_at IS NOT NULL OR
    m.source_record->>'notion_page_id' IS DISTINCT FROM r.destination_page_id::text OR
    NOT(m.source_record @> (w.last_acknowledged_values-'_edited_at'-'_archived')) THEN RAISE EXCEPTION 'Destination changed before source finish preparation'; END IF;
   UPDATE public.inventory_intake_submissions SET source_effect=source_effect||jsonb_build_object('readback',p_plan->'readback','status','finish_prepared') WHERE source_page_id=p_source_page_id;
  END IF;
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
