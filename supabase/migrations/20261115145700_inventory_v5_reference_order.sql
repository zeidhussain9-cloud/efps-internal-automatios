-- STAGED ONLY. Stable reference numbering is independent of other view sorts.
BEGIN;
ALTER TABLE public.inventory_renumber_jobs ADD COLUMN IF NOT EXISTS active_effect jsonb;
CREATE OR REPLACE FUNCTION public.inventory_v5_reference_order(p_operation text,
 p_page_id uuid DEFAULT NULL,p_listing_id text DEFAULT NULL,p_seed jsonb DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE ids uuid[]; digest text; j bigint;
BEGIN
 -- Serialize membership snapshots and job coalescing across concurrent inserts.
 PERFORM pg_advisory_xact_lock(55151126);
 IF p_operation='seed' THEN
  IF EXISTS(SELECT 1 FROM public.inventory_reference_order) THEN RAISE EXCEPTION 'Reference order already seeded'; END IF;
  IF jsonb_typeof(p_seed) IS DISTINCT FROM 'array' OR jsonb_array_length(p_seed)=0 THEN RAISE EXCEPTION 'Nonempty reviewed seed required'; END IF;
  INSERT INTO public.inventory_reference_order(page_id,listing_id,seeded_rank)
   SELECT (v->>'page_id')::uuid,v->>'listing_id',ordinality::integer
   FROM jsonb_array_elements(p_seed) WITH ORDINALITY AS x(v,ordinality);
 ELSIF p_operation='activate' THEN
  IF p_page_id IS NULL OR p_listing_id IS NULL OR p_listing_id='' THEN RAISE EXCEPTION 'Identity required'; END IF;
  INSERT INTO public.inventory_reference_order(page_id,listing_id) VALUES(p_page_id,p_listing_id)
   ON CONFLICT(page_id) DO UPDATE SET active=true WHERE inventory_reference_order.listing_id=excluded.listing_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Reference identity conflict'; END IF;
 ELSIF p_operation='deactivate' THEN
  UPDATE public.inventory_reference_order SET active=false WHERE page_id=p_page_id AND listing_id=p_listing_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Reference identity missing'; END IF;
 ELSIF p_operation NOT IN ('snapshot','read') THEN RAISE EXCEPTION 'Unsupported reference operation';
 END IF;
 SELECT coalesce(array_agg(page_id ORDER BY (seeded_rank IS NULL) DESC,
   CASE WHEN seeded_rank IS NULL THEN insertion_sequence END DESC,seeded_rank ASC),ARRAY[]::uuid[])
 INTO ids FROM public.inventory_reference_order WHERE active;
 -- MD5 is a non-security content key, not authentication.
 digest=md5(array_to_string(ids,','));
 IF p_operation <> 'read' AND NOT EXISTS(SELECT 1 FROM
   (SELECT membership_hash,status FROM public.inventory_renumber_jobs ORDER BY job_id DESC LIMIT 1) latest
   WHERE latest.membership_hash=digest AND latest.status IN ('pending','running','completed')) THEN
  UPDATE public.inventory_renumber_jobs SET status='superseded',updated_at=clock_timestamp() WHERE status='pending';
  INSERT INTO public.inventory_renumber_jobs(membership_hash,ordered_page_ids,status) VALUES(digest,ids,'pending') RETURNING job_id INTO j;
 END IF;
 RETURN jsonb_build_object('page_ids',to_jsonb(ids),'membership_hash',digest,'new_job_id',j);
END $$;
CREATE OR REPLACE FUNCTION public.inventory_v5_renumber_state(p_operation text,
 p_job_id bigint DEFAULT NULL,p_lease uuid DEFAULT NULL,p_next_offset integer DEFAULT NULL,p_error text DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_renumber_jobs%ROWTYPE; token uuid;
BEGIN
 PERFORM pg_advisory_xact_lock(55151126);
 IF p_operation='claim' THEN
  SELECT * INTO r FROM public.inventory_renumber_jobs WHERE status='running' FOR UPDATE;
  IF FOUND AND r.active_effect IS NOT NULL THEN
   INSERT INTO public.inventory_effect_recovery_incidents(scope,page_id,job_id,effect) VALUES('renumber',(r.active_effect->'intent'->>'page_id')::uuid,r.job_id,r.active_effect) ON CONFLICT(scope,effect) DO NOTHING;
   RETURN jsonb_build_object('busy',true,'needs_recovery',true); END IF;
  IF FOUND AND r.lease_until>clock_timestamp() THEN RETURN jsonb_build_object('busy',true); END IF;
  IF NOT FOUND THEN
   SELECT * INTO r FROM public.inventory_renumber_jobs WHERE status='pending' ORDER BY job_id DESC LIMIT 1 FOR UPDATE;
   IF NOT FOUND THEN RETURN jsonb_build_object('idle',true); END IF;
  END IF;
  token=gen_random_uuid();
  UPDATE public.inventory_renumber_jobs SET status='running',lease_token=token,
   lease_until=clock_timestamp()+interval '90 seconds',updated_at=clock_timestamp() WHERE job_id=r.job_id RETURNING * INTO r;
  RETURN to_jsonb(r);
 END IF;
 SELECT * INTO r FROM public.inventory_renumber_jobs WHERE job_id=p_job_id FOR UPDATE;
 IF NOT FOUND OR r.status<>'running' OR r.lease_token IS DISTINCT FROM p_lease OR r.lease_until<=clock_timestamp() THEN RAISE EXCEPTION 'Stale renumber lease'; END IF;
 IF r.active_effect IS NOT NULL AND p_operation NOT IN ('renew','end_effect') THEN RAISE EXCEPTION 'Uncertain title effect requires reconciliation'; END IF;
 IF p_operation='begin_effect' THEN
  IF p_error IS NULL THEN RAISE EXCEPTION 'Title effect intent required'; END IF;
  UPDATE public.inventory_renumber_jobs SET active_effect=jsonb_build_object('intent',p_error::jsonb,'lease',p_lease,'started_at',clock_timestamp()) WHERE job_id=p_job_id;
 ELSIF p_operation='end_effect' THEN
  IF r.active_effect IS NULL OR r.active_effect->>'lease' IS DISTINCT FROM p_lease::text THEN RAISE EXCEPTION 'Title effect ticket mismatch'; END IF;
  UPDATE public.inventory_renumber_jobs SET active_effect=NULL WHERE job_id=p_job_id;
 ELSIF p_operation='renew' THEN
  UPDATE public.inventory_renumber_jobs SET lease_until=clock_timestamp()+interval '90 seconds' WHERE job_id=p_job_id;
 ELSIF p_operation='checkpoint' THEN
  IF p_next_offset IS NULL OR p_next_offset<r.next_offset OR p_next_offset>cardinality(r.ordered_page_ids) THEN RAISE EXCEPTION 'Invalid renumber checkpoint'; END IF;
  UPDATE public.inventory_renumber_jobs SET next_offset=p_next_offset,updated_at=clock_timestamp() WHERE job_id=p_job_id;
 ELSIF p_operation='finish' THEN
  IF r.next_offset<>cardinality(r.ordered_page_ids) THEN RAISE EXCEPTION 'Renumber incomplete'; END IF;
  UPDATE public.inventory_renumber_jobs SET status='completed',lease_token=NULL,lease_until=NULL,updated_at=clock_timestamp() WHERE job_id=p_job_id;
 ELSIF p_operation='yield' THEN
  UPDATE public.inventory_renumber_jobs SET lease_until=clock_timestamp()-interval '1 second',updated_at=clock_timestamp() WHERE job_id=p_job_id;
 ELSIF p_operation='fail' THEN
  UPDATE public.inventory_renumber_jobs SET status='failed',error=left(p_error,1800),lease_token=NULL,lease_until=NULL,updated_at=clock_timestamp() WHERE job_id=p_job_id;
 ELSE RAISE EXCEPTION 'Unsupported renumber transition';
 END IF;
 RETURN jsonb_build_object('ok',true);
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_reference_order FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.inventory_v5_renumber_state FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_reference_order TO service_role;
GRANT EXECUTE ON FUNCTION public.inventory_v5_renumber_state TO service_role;
COMMIT;
