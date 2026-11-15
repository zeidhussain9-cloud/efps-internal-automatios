-- STAGED. Fenced worker state transitions. Notion itself has no CAS operation.
BEGIN;
CREATE TABLE public.inventory_effect_recovery_incidents(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 scope text NOT NULL CHECK(scope IN ('worker','renumber')),page_id uuid,job_id bigint,
 effect jsonb NOT NULL,status text NOT NULL DEFAULT 'blocked',
 readback jsonb,remaining jsonb,state_hash text,decision jsonb,attestation_id uuid,
 reported_at timestamptz NOT NULL DEFAULT clock_timestamp(),resolved_at timestamptz,
 UNIQUE(scope,effect)
);
ALTER TABLE public.inventory_effect_recovery_incidents ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_effect_recovery_incidents FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.inventory_effect_recovery_incidents TO service_role;
ALTER TABLE public.inventory_processing_revisions ADD COLUMN IF NOT EXISTS active_effect jsonb;
ALTER TABLE public.inventory_processing_revisions ADD COLUMN IF NOT EXISTS prepared_inputs jsonb;
ALTER TABLE public.inventory_processing_revisions ADD COLUMN IF NOT EXISTS page_id uuid UNIQUE;
ALTER TABLE public.inventory_processing_revisions ADD COLUMN IF NOT EXISTS field_provenance jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE public.inventory_processing_revisions ADD COLUMN IF NOT EXISTS source_evidence jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE public.inventory_processing_revisions ADD COLUMN IF NOT EXISTS review_history jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE public.inventory_processing_revisions ADD COLUMN IF NOT EXISTS processing_status text NOT NULL DEFAULT 'pending';

CREATE OR REPLACE FUNCTION public.inventory_v5_worker_state(
 p_operation text,p_page_id uuid,p_listing_id text DEFAULT NULL,p_lease uuid DEFAULT NULL,
 p_revision bigint DEFAULT NULL,p_values jsonb DEFAULT NULL,p_patch jsonb DEFAULT NULL,
 p_provenance jsonb DEFAULT NULL,p_input_hash text DEFAULT NULL,p_status text DEFAULT NULL,
 p_review jsonb DEFAULT NULL
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_processing_revisions%ROWTYPE; token uuid;
BEGIN
 IF p_operation='claim' THEN
  IF p_listing_id IS NULL OR p_listing_id='' THEN RAISE EXCEPTION 'Listing identity required'; END IF;
  INSERT INTO public.inventory_processing_revisions(listing_id,page_id)
  VALUES(p_listing_id,p_page_id) ON CONFLICT(listing_id) DO NOTHING;
  SELECT * INTO r FROM public.inventory_processing_revisions WHERE page_id=p_page_id FOR UPDATE;
  IF r.listing_id IS DISTINCT FROM p_listing_id THEN RAISE EXCEPTION 'Page/listing identity conflict'; END IF;
  IF r.lease_until > clock_timestamp() THEN RETURN jsonb_build_object('busy',true); END IF;
  IF r.active_effect IS NOT NULL THEN
   INSERT INTO public.inventory_effect_recovery_incidents(scope,page_id,effect) VALUES('worker',p_page_id,r.active_effect) ON CONFLICT(scope,effect) DO NOTHING;
   RETURN jsonb_build_object('needs_recovery',true,'busy',true); END IF;
  IF r.lease_until > clock_timestamp() THEN RETURN jsonb_build_object('busy',true); END IF;
  token=gen_random_uuid();
  UPDATE public.inventory_processing_revisions SET lease_token=token,
    lease_until=clock_timestamp()+interval '90 seconds',updated_at=clock_timestamp()
    WHERE page_id=p_page_id;
  RETURN jsonb_build_object('lease',token,'revision',r.revision);
 END IF;
 SELECT * INTO r FROM public.inventory_processing_revisions WHERE page_id=p_page_id FOR UPDATE;
 IF p_operation='record_effect_receipt' THEN
  IF NOT FOUND OR r.active_effect->>'lease' IS DISTINCT FROM p_lease::text OR r.active_effect ? 'receipt' OR jsonb_typeof(p_values) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Receipt effect mismatch'; END IF;
  UPDATE public.inventory_processing_revisions SET active_effect=active_effect||jsonb_build_object('receipt',p_values||jsonb_build_object('effect_token',p_lease,'page_id',p_page_id)) WHERE page_id=p_page_id;
  INSERT INTO public.inventory_effect_recovery_incidents(scope,page_id,effect,status,decision) VALUES('worker',p_page_id,r.active_effect,'terminal_receipt_recorded',p_values) ON CONFLICT(scope,effect) DO UPDATE SET decision=excluded.decision;
  RETURN jsonb_build_object('ok',true);
 END IF;
 IF NOT FOUND OR r.lease_token IS DISTINCT FROM p_lease OR r.lease_until <= clock_timestamp() THEN
  RAISE EXCEPTION 'Stale or expired inventory lease';
 END IF;
 IF p_operation='load' THEN RETURN to_jsonb(r); END IF;
 IF r.active_effect IS NOT NULL AND p_operation IN ('prepare','finish') THEN RAISE EXCEPTION 'External effect unresolved'; END IF;
 IF p_operation='renew' THEN
  UPDATE public.inventory_processing_revisions SET lease_until=clock_timestamp()+interval '90 seconds' WHERE page_id=p_page_id;
 ELSIF p_operation='begin_effect' THEN
  IF r.active_effect IS NOT NULL THEN RAISE EXCEPTION 'Uncertain external effect requires reconciliation'; END IF;
  IF jsonb_typeof(p_values) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Effect intent required'; END IF;
  UPDATE public.inventory_processing_revisions SET active_effect=jsonb_build_object('intent',p_values,'lease',p_lease,'started_at',clock_timestamp()),updated_at=clock_timestamp() WHERE page_id=p_page_id;
 ELSIF p_operation='end_effect' THEN
  IF r.active_effect IS NULL OR r.active_effect->>'lease' IS DISTINCT FROM p_lease::text THEN RAISE EXCEPTION 'Effect ticket mismatch'; END IF;
  UPDATE public.inventory_effect_recovery_incidents SET status='completed',resolved_at=clock_timestamp() WHERE scope='worker' AND (effect=r.active_effect OR effect=r.active_effect-'receipt') AND status IN ('blocked','terminal_receipt_recorded');
  UPDATE public.inventory_processing_revisions SET active_effect=NULL,updated_at=clock_timestamp() WHERE page_id=p_page_id;
 ELSIF p_operation='prepare' THEN
  IF p_revision IS DISTINCT FROM r.revision THEN RAISE EXCEPTION 'Inventory revision conflict'; END IF;
  IF jsonb_typeof(p_patch) IS DISTINCT FROM 'object' OR jsonb_typeof(p_provenance) IS DISTINCT FROM 'object' OR jsonb_typeof(p_values) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Patch/provenance/inputs object required'; END IF;
  UPDATE public.inventory_processing_revisions SET pending_patch=p_patch,expected_self_write=p_patch,
   field_provenance=p_provenance,current_input_hash=p_input_hash,prepared_inputs=p_values,processing_status='prepared',updated_at=clock_timestamp()
   WHERE page_id=p_page_id;
  INSERT INTO public.inventory_field_provenance(listing_id,field_name,origin,evidence,inputs_hash,derivation_version,last_generated_value,revision)
   SELECT r.listing_id,key,value->>'origin',value,p_input_hash,
    (value->>'derivation_version')::integer,value->'last_generated_value',r.revision+1
   FROM jsonb_each(p_provenance)
   ON CONFLICT(listing_id,field_name) DO UPDATE SET origin=excluded.origin,evidence=excluded.evidence,
    inputs_hash=excluded.inputs_hash,derivation_version=excluded.derivation_version,
    last_generated_value=excluded.last_generated_value,revision=excluded.revision,updated_at=clock_timestamp();
 ELSIF p_operation='finish' THEN
  IF jsonb_typeof(p_values) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Acknowledged object required'; END IF;
  UPDATE public.inventory_processing_revisions SET last_acknowledged_values=p_values,pending_patch=NULL,prepared_inputs=NULL,
    revision=revision+1,processing_status=CASE WHEN p_values->>'Pipeline Status'='Needs Review' THEN 'needs_review' ELSE p_status END,updated_at=clock_timestamp() WHERE page_id=p_page_id;
 ELSIF p_operation='review' THEN
  IF jsonb_typeof(p_review) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Review object required'; END IF;
  UPDATE public.inventory_processing_revisions SET review_history=review_history||jsonb_build_array(p_review),
    processing_status='needs_review',updated_at=clock_timestamp() WHERE page_id=p_page_id;
 ELSIF p_operation='requeue' THEN
  UPDATE public.inventory_processing_revisions SET processing_status='retry',updated_at=clock_timestamp() WHERE page_id=p_page_id;
 ELSIF p_operation='release' THEN
  UPDATE public.inventory_processing_revisions SET lease_token=NULL,lease_until=NULL,updated_at=clock_timestamp() WHERE page_id=p_page_id;
 ELSE RAISE EXCEPTION 'Unsupported inventory state operation';
 END IF;
 RETURN jsonb_build_object('ok',true);
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_worker_state FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_worker_state TO service_role;
COMMIT;
