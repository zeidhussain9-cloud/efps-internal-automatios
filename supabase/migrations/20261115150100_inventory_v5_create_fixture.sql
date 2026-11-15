-- STAGED FIXTURE ONLY. Never enable in production without draft visibility policy.
BEGIN;
CREATE TABLE public.inventory_v5_creations(
 source_page_id uuid PRIMARY KEY,payload_hash text NOT NULL,listing_id text NOT NULL UNIQUE,
 source_before jsonb NOT NULL,schema_contract jsonb NOT NULL,policy jsonb NOT NULL,onboarded_at timestamptz NOT NULL,
 phase text NOT NULL DEFAULT 'reserved',output jsonb,plan jsonb,effect jsonb,page_id uuid UNIQUE,
 lease uuid,lease_until timestamptz,baseline jsonb,provenance jsonb,full_readback jsonb);
ALTER TABLE public.inventory_v5_creations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_v5_creations FROM PUBLIC,anon,authenticated;
CREATE TABLE public.inventory_v5_create_receipts(request_id text PRIMARY KEY,source_page_id uuid NOT NULL,effect_id uuid NOT NULL,receipt jsonb NOT NULL);
ALTER TABLE public.inventory_v5_create_receipts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_v5_create_receipts FROM PUBLIC,anon,authenticated;
-- Same established allocation format, UTC month and source reuse. New immutable
-- reservations participate in collision checks. Never adopt a later legacy ID.
CREATE OR REPLACE FUNCTION public.crm_allocate_notion_inventory_listing_id(p_source_page_id text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE v_listing_id text;v_suffix text;v_alphabet constant text:='0123456789ABCDEFGHJKMNPQRSTVWXYZ';v_i integer;
BEGIN
 PERFORM pg_advisory_xact_lock(104729,82);
 IF EXISTS(SELECT 1 FROM public.inventory_v5_creations WHERE source_page_id::text=p_source_page_id) THEN RAISE EXCEPTION 'V5 creation reservation requires its controller, not legacy allocator'; END IF;
 SELECT listing_id INTO v_listing_id FROM public.crm_inventory_intake_events WHERE source_page_id=p_source_page_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Notion page must be claimed before allocating a Listing ID'; END IF;
 IF v_listing_id IS NOT NULL THEN
  IF EXISTS(SELECT 1 FROM public.inventory_v5_creations WHERE listing_id=v_listing_id AND source_page_id::text<>p_source_page_id) OR
   EXISTS(SELECT 1 FROM public.inventory_v5_creations WHERE source_page_id::text=p_source_page_id AND listing_id<>v_listing_id) THEN RAISE EXCEPTION 'Immutable create reservation differs'; END IF;
  RETURN v_listing_id;
 END IF;
 IF EXISTS(SELECT 1 FROM public.inventory_v5_creations WHERE source_page_id::text=p_source_page_id) THEN RAISE EXCEPTION 'Reserved identity missing from legacy ledger'; END IF;
 FOR attempt IN 1..100 LOOP
  v_suffix='';
  FOR v_i IN 1..4 LOOP v_suffix=v_suffix||substr(v_alphabet,floor(random()*length(v_alphabet))::integer+1,1); END LOOP;
  v_listing_id='EF-'||to_char(now() AT TIME ZONE 'UTC','YYMM')||'-'||v_suffix;
  EXIT WHEN NOT EXISTS(SELECT 1 FROM public.crm_inventory_snapshot WHERE listing_id=v_listing_id
    UNION ALL SELECT 1 FROM public.crm_inventory_intake_events WHERE listing_id=v_listing_id
    UNION ALL SELECT 1 FROM public.inventory_v5_creations WHERE listing_id=v_listing_id);
  v_listing_id=NULL;
 END LOOP;
 IF v_listing_id IS NULL THEN RAISE EXCEPTION 'Unable to allocate a unique Listing ID'; END IF;
 UPDATE public.crm_inventory_intake_events SET listing_id=v_listing_id,updated_at=now() WHERE source_page_id=p_source_page_id;
 RETURN v_listing_id;
END $$;
-- Fence legacy source claims without resetting any V5 in-flight reservation.
-- Existing legacy algorithm otherwise preserved from fresh management evidence.
CREATE OR REPLACE FUNCTION public.crm_claim_notion_inventory_intake(p_source_page_id text,p_payload_hash text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE v_row public.crm_inventory_intake_events%ROWTYPE;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended(p_source_page_id,1));
 IF EXISTS(SELECT 1 FROM public.inventory_v5_creations WHERE source_page_id::text=p_source_page_id) THEN
  RETURN jsonb_build_object('status','in_progress','v5_create_held',true);
 END IF;
 INSERT INTO public.crm_inventory_intake_events(source_page_id,payload_hash,processing_status)
  VALUES(p_source_page_id,p_payload_hash,'processing') ON CONFLICT(source_page_id) DO NOTHING RETURNING * INTO v_row;
 IF FOUND THEN RETURN jsonb_build_object('status','claimed','item',to_jsonb(v_row)); END IF;
 SELECT * INTO v_row FROM public.crm_inventory_intake_events WHERE source_page_id=p_source_page_id FOR UPDATE;
 IF v_row.processing_status='processed' AND v_row.payload_hash=p_payload_hash THEN RETURN jsonb_build_object('status','duplicate','item',to_jsonb(v_row)); END IF;
 IF v_row.processing_status='processing' AND v_row.updated_at>now()-interval '5 minutes' THEN RETURN jsonb_build_object('status','in_progress','item',to_jsonb(v_row)); END IF;
 UPDATE public.crm_inventory_intake_events SET payload_hash=p_payload_hash,processing_status='processing',updated_at=now(),processed_at=NULL
  WHERE source_page_id=p_source_page_id RETURNING * INTO v_row;
 RETURN jsonb_build_object('status','claimed','item',to_jsonb(v_row));
END $$;
CREATE OR REPLACE FUNCTION public.inventory_v5_create_fixture(p_operation text,p_source uuid,p_payload text DEFAULT NULL,
 p_lease uuid DEFAULT NULL,p_value jsonb DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_v5_creations%ROWTYPE;token uuid;id text;legacy jsonb;s public.crm_inventory_snapshot%ROWTYPE;v jsonb;membership jsonb;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended(p_source::text,1));
 IF p_operation='claim' THEN
  SELECT * INTO r FROM public.inventory_v5_creations WHERE source_page_id=p_source FOR UPDATE;
  IF NOT FOUND THEN
   IF coalesce(p_payload,'') !~ '^[a-f0-9]{64}$' OR p_value->'policy'->>'visibility' IS DISTINCT FROM 'isolated_fixture_only' OR
    jsonb_typeof(p_value->'source_before') IS DISTINCT FROM 'object' OR jsonb_typeof(p_value->'schema') IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Exact isolated creation contract required'; END IF;
   SELECT to_jsonb(x) INTO legacy FROM public.crm_inventory_intake_events x WHERE source_page_id=p_source::text FOR UPDATE;
   IF legacy IS NULL THEN
    INSERT INTO public.crm_inventory_intake_events(source_page_id,payload_hash,processing_status) VALUES(p_source::text,p_payload,'processing');
   ELSE RAISE EXCEPTION 'Preexisting legacy claim may have external work; explicit terminal review required'; END IF;
   id=public.crm_allocate_notion_inventory_listing_id(p_source::text);
   INSERT INTO public.inventory_v5_creations(source_page_id,payload_hash,listing_id,source_before,schema_contract,policy,onboarded_at)
    VALUES(p_source,p_payload,id,p_value->'source_before',p_value->'schema',p_value->'policy',(p_value->>'onboarded_at')::timestamptz) RETURNING * INTO r;
  ELSE
   SELECT to_jsonb(x) INTO legacy FROM public.crm_inventory_intake_events x WHERE source_page_id=p_source::text;
   IF r.payload_hash IS DISTINCT FROM p_payload OR r.source_before IS DISTINCT FROM p_value->'source_before' OR
    r.schema_contract IS DISTINCT FROM p_value->'schema' OR r.policy IS DISTINCT FROM p_value->'policy' OR
    r.onboarded_at IS DISTINCT FROM (p_value->>'onboarded_at')::timestamptz OR legacy->>'listing_id' IS DISTINCT FROM r.listing_id THEN
    RAISE EXCEPTION 'Immutable allocated source contract differs'; END IF;
  END IF;
  IF r.lease_until>clock_timestamp() THEN RETURN jsonb_build_object('held',true); END IF;
  IF r.effect IS NOT NULL AND NOT(r.effect ? 'receipt') THEN RETURN jsonb_build_object('held',true,'unknown_create',true); END IF;
  IF r.phase='pipeline_running' THEN RETURN jsonb_build_object('held',true,'uncaptured_pipeline',true); END IF;
  token=gen_random_uuid();
  UPDATE public.inventory_v5_creations SET lease=token,lease_until=clock_timestamp()+interval '90 seconds' WHERE source_page_id=p_source RETURNING * INTO r;
  RETURN to_jsonb(r);
 END IF;
 SELECT * INTO r FROM public.inventory_v5_creations WHERE source_page_id=p_source FOR UPDATE;
 IF NOT FOUND OR r.lease IS DISTINCT FROM p_lease OR r.lease_until<=clock_timestamp() THEN RAISE EXCEPTION 'Stale creation lease'; END IF;
 SELECT to_jsonb(x) INTO legacy FROM public.crm_inventory_intake_events x WHERE source_page_id=p_source::text;
 IF legacy->>'listing_id' IS DISTINCT FROM r.listing_id THEN RAISE EXCEPTION 'Legacy identity changed after reservation'; END IF;
 IF p_operation='renew' THEN
  UPDATE public.inventory_v5_creations SET lease_until=clock_timestamp()+interval '90 seconds' WHERE source_page_id=p_source;
 ELSIF p_operation='pipeline_begin' THEN
  IF r.phase<>'reserved' THEN RAISE EXCEPTION 'Single pipeline run required'; END IF;
  UPDATE public.inventory_v5_creations SET phase='pipeline_running' WHERE source_page_id=p_source;
 ELSIF p_operation='pipeline_output' THEN
  IF r.phase<>'pipeline_running' OR r.output IS NOT NULL OR p_value->'processed'->>'listing_id' IS DISTINCT FROM r.listing_id OR
   coalesce(p_value->'processed'->>'status','') NOT IN ('Pending','Needs Review') OR jsonb_typeof(p_value->'issues') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'Exact actual pipeline output required'; END IF;
  UPDATE public.inventory_v5_creations SET output=p_value,phase='output_saved' WHERE source_page_id=p_source;
 ELSIF p_operation='plan' THEN
  IF r.phase<>'output_saved' OR r.plan IS NOT NULL OR p_value->'body'->'parent'->>'database_id' IS DISTINCT FROM 'bccfd4f55e294b269daa093a928f873a' OR
   p_value->>'values_hash_input' IS NULL OR (p_value->>'values_hash_input')::jsonb IS DISTINCT FROM p_value->'values' OR
   p_value->>'values_hash' IS DISTINCT FROM encode(sha256(convert_to(p_value->>'values_hash_input','UTF8')),'hex') OR
   coalesce(p_value->>'body_hash','') !~ '^[a-f0-9]{64}$' OR p_value->'values'->>'listing_id' IS DISTINCT FROM r.listing_id OR
   p_value->'body'->'template' IS NOT NULL OR p_value->'values'->>'SL number' IS DISTINCT FROM '' OR
   p_value->'values'->>'Availability' IS DISTINCT FROM r.policy->>'availability' OR p_value->'values'->>'Pipeline Status' IS DISTINCT FROM 'Processing' OR
   p_value->'values'->'Live On' IS DISTINCT FROM '[]'::jsonb THEN RAISE EXCEPTION 'Exact fixture-only create body required'; END IF;
  UPDATE public.inventory_v5_creations SET plan=p_value,phase='planned' WHERE source_page_id=p_source;
 ELSIF p_operation='begin' THEN
  IF r.phase<>'planned' OR r.effect IS NOT NULL OR p_value->'source' IS DISTINCT FROM r.source_before OR
   p_value->'schema' IS DISTINCT FROM r.schema_contract THEN RAISE EXCEPTION 'Exact precreate source/schema required'; END IF;
  token=gen_random_uuid();
  UPDATE public.inventory_v5_creations SET effect=jsonb_build_object('nonce',token),phase='dispatching' WHERE source_page_id=p_source;
  RETURN jsonb_build_object('nonce',token);
 ELSIF p_operation='dispatch' THEN
  IF r.phase<>'dispatching' OR r.effect ? 'dispatch' OR p_value->>'nonce' IS DISTINCT FROM r.effect->>'nonce' OR
   p_value->>'method' IS DISTINCT FROM 'POST' OR p_value->>'url' IS DISTINCT FROM 'https://api.notion.com/v1/pages' OR
   p_value->>'body_hash' IS DISTINCT FROM r.plan->>'body_hash' OR p_value->'parent' IS DISTINCT FROM r.plan->'body'->'parent' THEN RAISE EXCEPTION 'Exact POST dispatch required'; END IF;
  UPDATE public.inventory_v5_creations SET effect=effect||jsonb_build_object('dispatch',p_value) WHERE source_page_id=p_source;
 ELSIF p_operation='receipt' THEN
  IF r.phase<>'dispatching' OR r.effect ? 'receipt' OR p_value->'dispatch' IS DISTINCT FROM r.effect->'dispatch' OR
   r.effect->'dispatch' IS NULL OR coalesce(p_value->>'status','') !~ '^2[0-9][0-9]$' OR coalesce(p_value->>'request_id','')='' OR
   coalesce(p_value->>'page_id','') !~ '^[0-9a-f-]{36}$' OR p_value->'body'->>'id' IS DISTINCT FROM p_value->>'page_id' OR
   p_value->'body'->'parent'->>'database_id' IS DISTINCT FROM r.plan->'body'->'parent'->>'database_id' THEN RAISE EXCEPTION 'Full terminal create response required'; END IF;
  INSERT INTO public.inventory_v5_create_receipts VALUES(p_value->>'request_id',p_source,(r.effect->>'nonce')::uuid,p_value);
  UPDATE public.inventory_v5_creations SET page_id=(p_value->>'page_id')::uuid,effect=effect||jsonb_build_object('receipt',p_value),phase='receipted' WHERE source_page_id=p_source;
 ELSIF p_operation='bootstrap' THEN
  IF r.phase NOT IN ('receipted','bootstrapped') OR r.effect->'receipt' IS NULL OR p_value->'values' IS DISTINCT FROM r.plan->'values' OR
   p_value->'source' IS DISTINCT FROM r.source_before OR p_value->'schema' IS DISTINCT FROM r.schema_contract OR
   replace(p_value->'readback'->>'id','-','') IS DISTINCT FROM replace(r.page_id::text,'-','') OR p_value->'readback'->>'archived' IS DISTINCT FROM 'false' OR
   p_value->'readback'->'parent'->>'database_id' IS DISTINCT FROM r.plan->'body'->'parent'->>'database_id' OR
   NOT((p_value->'readback'->'values') @> (r.plan->'values')) OR
   jsonb_typeof(p_value->'provenance') IS DISTINCT FROM 'object' OR
   (SELECT array_agg(key ORDER BY key) FROM jsonb_each(p_value->'provenance')) IS DISTINCT FROM (SELECT array_agg(key ORDER BY key) FROM jsonb_each(r.plan->'values')) OR
   (SELECT count(*) FROM jsonb_each(p_value->'provenance'))<>(SELECT count(*) FROM jsonb_each(r.plan->'values')) OR
   EXISTS(SELECT 1 FROM jsonb_each(p_value->'provenance') x WHERE x.value->>'origin' IS DISTINCT FROM 'legacy_unknown' OR
      x.value->'created_value' IS DISTINCT FROM r.plan->'values'->x.key OR x.value->>'create_nonce' IS DISTINCT FROM r.effect->>'nonce') THEN RAISE EXCEPTION 'Exact receipt-proven unknown-ownership bootstrap required'; END IF;
  s=jsonb_populate_record(NULL::public.crm_inventory_snapshot,p_value->'mirror');
  IF jsonb_typeof(p_value->'mirror') IS DISTINCT FROM 'object' OR
   EXISTS(SELECT 1 FROM jsonb_object_keys(p_value->'mirror') k WHERE k NOT IN
    ('listing_id','source_kind','source_tab','source_record','locality','society_name','bhk','furnishing','monthly_rent','pet_friendly','cloudinary_image_urls',
     'source_hash','inventory_contract_version','inventory_revision','availability','listing_state','pipeline_status','business_status','intake_status','live_on','onboarded_at','deleted_at')) OR
   s.source_kind IS DISTINCT FROM 'housing_notion' OR s.source_tab IS DISTINCT FROM 'Housing Listings' OR
   s.deleted_at IS NOT NULL OR s.intake_status IS DISTINCT FROM 'Processing' OR
   s.source_hash IS DISTINCT FROM r.plan->>'values_hash' OR
   s.listing_id IS DISTINCT FROM r.listing_id OR s.source_record->>'notion_page_id' IS DISTINCT FROM r.page_id::text OR
   s.source_record IS DISTINCT FROM (r.plan->'values')||jsonb_build_object('notion_page_id',r.page_id,'inventory_contract_version',5) OR
   s.inventory_revision IS DISTINCT FROM 1 OR s.inventory_contract_version IS DISTINCT FROM 5 OR s.availability IS DISTINCT FROM r.policy->>'availability' OR
   s.locality IS DISTINCT FROM coalesce(r.plan->'values'->>'locality','') OR s.society_name IS DISTINCT FROM coalesce(r.plan->'values'->>'society_name','') OR
   s.bhk IS DISTINCT FROM coalesce(r.plan->'values'->>'BHK','') OR s.furnishing IS DISTINCT FROM coalesce(r.plan->'values'->>'furnish_type','') OR
   s.pet_friendly IS DISTINCT FROM coalesce(r.plan->'values'->>'pet_friendly','') OR
   s.monthly_rent IS DISTINCT FROM nullif(r.plan->'values'->>'monthly_rent','')::numeric OR
   s.cloudinary_image_urls IS DISTINCT FROM coalesce((SELECT jsonb_agg(btrim(x)) FROM unnest(string_to_array(coalesce(r.plan->'values'->>'cloudinary_image_urls',''),','))x WHERE btrim(x)<>''),'[]'::jsonb) OR
   s.listing_state IS DISTINCT FROM r.policy->>'availability' OR s.business_status IS DISTINCT FROM 'Processing' OR
   s.pipeline_status IS DISTINCT FROM 'Processing' OR s.live_on IS DISTINCT FROM ARRAY[]::text[] OR s.onboarded_at IS DISTINCT FROM r.onboarded_at THEN RAISE EXCEPTION 'Exact mirror bootstrap required'; END IF;
  IF r.phase='bootstrapped' THEN
   IF r.baseline IS DISTINCT FROM p_value->'values' OR r.provenance IS DISTINCT FROM p_value->'provenance' OR r.full_readback IS DISTINCT FROM p_value->'readback' OR r.source_before IS DISTINCT FROM p_value->'source' OR r.schema_contract IS DISTINCT FROM p_value->'schema' THEN RAISE EXCEPTION 'Bootstrap immutable'; END IF;
   RETURN jsonb_build_object('ok',true,'source_completion_allowed',false,'phase','bootstrapped');
  END IF;
  -- Mirror receipt times are database-owned bootstrap observations, not onboarding.
  s.source_snapshot_at=clock_timestamp();s.last_synced_at=s.source_snapshot_at;
  INSERT INTO public.inventory_processing_revisions(listing_id,page_id,last_acknowledged_values,field_provenance,revision,processing_status)
   VALUES(r.listing_id,r.page_id,(r.plan->'values')||jsonb_build_object('_archived',false),p_value->'provenance',1,'create_fixture_draft');
  INSERT INTO public.inventory_field_provenance(listing_id,field_name,origin,evidence,revision)
   SELECT r.listing_id,key,'legacy_unknown',value,1 FROM jsonb_each(p_value->'provenance');
  INSERT INTO public.crm_inventory_snapshot SELECT s.*;
  membership=public.inventory_v5_reference_order('activate',r.page_id,r.listing_id);
  UPDATE public.inventory_v5_creations SET baseline=p_value->'values',provenance=p_value->'provenance',full_readback=p_value->'readback',phase='bootstrapped' WHERE source_page_id=p_source;
  RETURN jsonb_build_object('ok',true,'phase','bootstrapped','membership',membership,'source_completion_allowed',false);
 ELSIF p_operation='release' THEN
  UPDATE public.inventory_v5_creations SET lease=NULL,lease_until=NULL WHERE source_page_id=p_source;
 ELSE RAISE EXCEPTION 'Unknown fixture create operation'; END IF;
 RETURN jsonb_build_object('ok',true,'source_completion_allowed',false);
END $$;
REVOKE ALL ON FUNCTION public.crm_allocate_notion_inventory_listing_id FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.crm_claim_notion_inventory_intake FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.crm_allocate_notion_inventory_listing_id TO service_role;
GRANT EXECUTE ON FUNCTION public.crm_claim_notion_inventory_intake TO service_role;
REVOKE ALL ON FUNCTION public.inventory_v5_create_fixture FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_create_fixture TO service_role;
COMMIT;
