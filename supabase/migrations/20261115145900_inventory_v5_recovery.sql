-- STAGED ONLY. Operator-gated recovery, never timeout-based takeover.
BEGIN;
CREATE TABLE public.inventory_effect_recovery_attestations(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),scope text NOT NULL CHECK(scope IN ('worker','renumber')),
 page_id uuid NOT NULL,job_id bigint,effect jsonb NOT NULL,
 writer_reference text NOT NULL CHECK(length(writer_reference)>0),
 remote_reference text NOT NULL CHECK(length(remote_reference)>0),
 request_reference text NOT NULL CHECK(length(request_reference)>0),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),used_at timestamptz,
 CHECK((scope='worker' AND job_id IS NULL)OR(scope='renumber' AND job_id IS NOT NULL))
);
ALTER TABLE public.inventory_effect_recovery_attestations ENABLE ROW LEVEL SECURITY;
-- Only a database administrator may register independently checked proof.
-- The ordinary worker can read an attestation but cannot insert/update it.
REVOKE ALL ON public.inventory_effect_recovery_attestations FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT ON public.inventory_effect_recovery_attestations TO service_role;
CREATE OR REPLACE FUNCTION public.inventory_v5_recovery_snapshot(p_scope text,p_page_id uuid,p_job_id bigint DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_processing_revisions%ROWTYPE;j public.inventory_renumber_jobs%ROWTYPE;
BEGIN
 IF p_scope='worker' THEN
  SELECT * INTO r FROM public.inventory_processing_revisions WHERE page_id=p_page_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Recovery listing missing'; END IF;
  RETURN jsonb_build_object('effect',r.active_effect,'prepared_inputs',r.prepared_inputs,'pending_patch',r.pending_patch);
 ELSIF p_scope='renumber' THEN
  SELECT * INTO j FROM public.inventory_renumber_jobs WHERE job_id=p_job_id;
  IF NOT FOUND OR (j.active_effect->'intent'->>'page_id')::uuid IS DISTINCT FROM p_page_id THEN RAISE EXCEPTION 'Recovery title intent mismatch'; END IF;
  RETURN jsonb_build_object('effect',j.active_effect,'prepared_inputs',j.active_effect->'intent'->'before','pending_patch',j.active_effect->'intent'->'patch');
 ELSE RAISE EXCEPTION 'Invalid recovery scope'; END IF;
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_recovery_snapshot FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_recovery_snapshot TO service_role;
CREATE OR REPLACE FUNCTION public.inventory_v5_recover_effect(
 p_attestation uuid,p_expected_effect jsonb,p_current jsonb,p_remaining jsonb,p_state_hash text,p_decision jsonb)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE a public.inventory_effect_recovery_attestations%ROWTYPE;
 r public.inventory_processing_revisions%ROWTYPE;j public.inventory_renumber_jobs%ROWTYPE;
BEGIN
 SELECT * INTO a FROM public.inventory_effect_recovery_attestations WHERE id=p_attestation FOR UPDATE;
 IF NOT FOUND OR a.used_at IS NOT NULL OR a.effect IS DISTINCT FROM p_expected_effect THEN RAISE EXCEPTION 'Exact unused operator recovery attestation required'; END IF;
 IF jsonb_typeof(p_current) IS DISTINCT FROM 'object' OR jsonb_typeof(p_remaining) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Recovery readback objects required'; END IF;
 IF p_state_hash IS NULL OR length(p_state_hash)<>64 OR jsonb_typeof(p_decision) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'Durable recovery decision/hash required'; END IF;
 IF a.scope='worker' THEN
  SELECT * INTO r FROM public.inventory_processing_revisions WHERE page_id=a.page_id FOR UPDATE;
  IF NOT FOUND OR r.active_effect IS DISTINCT FROM p_expected_effect OR r.lease_until>clock_timestamp() THEN RAISE EXCEPTION 'Recovery effect changed or lease still active'; END IF;
  -- Leave pending intent for a fresh worker. No Notion write in reconciliation.
  UPDATE public.inventory_processing_revisions SET active_effect=NULL,lease_token=NULL,lease_until=NULL,
   processing_status='recovery_reconciled',updated_at=clock_timestamp() WHERE page_id=a.page_id;
 ELSE
  PERFORM pg_advisory_xact_lock(55151126);
  SELECT * INTO j FROM public.inventory_renumber_jobs WHERE job_id=a.job_id FOR UPDATE;
  IF NOT FOUND OR j.active_effect IS DISTINCT FROM p_expected_effect OR j.lease_until>clock_timestamp() OR j.status<>'running' THEN RAISE EXCEPTION 'Title recovery effect changed or lease still active'; END IF;
  UPDATE public.inventory_renumber_jobs SET active_effect=NULL,lease_token=NULL,lease_until=clock_timestamp()-interval '1 second',
   updated_at=clock_timestamp() WHERE job_id=a.job_id;
 END IF;
 INSERT INTO public.inventory_effect_recovery_incidents(scope,page_id,job_id,effect,status,readback,remaining,state_hash,decision,attestation_id,resolved_at)
 VALUES(a.scope,a.page_id,a.job_id,p_expected_effect,'reconciled',p_current,p_remaining,p_state_hash,p_decision,a.id,clock_timestamp())
 ON CONFLICT(scope,effect) DO UPDATE SET status='reconciled',readback=excluded.readback,remaining=excluded.remaining,
 state_hash=excluded.state_hash,decision=excluded.decision,attestation_id=excluded.attestation_id,resolved_at=excluded.resolved_at;
 UPDATE public.inventory_effect_recovery_attestations SET used_at=clock_timestamp() WHERE id=a.id;
 RETURN jsonb_build_object('status','reconciled_without_notion_write');
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_recover_effect FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_recover_effect TO service_role;
COMMIT;
