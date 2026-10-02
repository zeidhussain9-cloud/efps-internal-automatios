BEGIN;
ALTER TABLE public.crm_ai_cursors ADD COLUMN IF NOT EXISTS last_evaluated_message_id bigint,ADD COLUMN IF NOT EXISTS last_evaluated_message_at timestamptz,ADD COLUMN IF NOT EXISTS last_evaluated_at timestamptz;
ALTER TABLE public.crm_ai_runs ADD COLUMN IF NOT EXISTS invocation_source text NOT NULL DEFAULT 'ui_manual',ADD COLUMN IF NOT EXISTS checkpoint_message_id bigint,ADD COLUMN IF NOT EXISTS checkpoint_message_at timestamptz,ADD COLUMN IF NOT EXISTS eligibility_reason text,ADD COLUMN IF NOT EXISTS status_action text NOT NULL DEFAULT 'not_applicable',ADD COLUMN IF NOT EXISTS status_decided_at timestamptz,ADD COLUMN IF NOT EXISTS status_decided_by text,ADD COLUMN IF NOT EXISTS idempotency_key text;
CREATE UNIQUE INDEX IF NOT EXISTS crm_ai_runs_idempotency_key_uidx ON public.crm_ai_runs(idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS crm_ai_runs_scheduler_lookup_idx ON public.crm_ai_runs(lead_id,invocation_source,checkpoint_message_id,created_at DESC);
CREATE INDEX IF NOT EXISTS crm_ai_cursors_evaluation_idx ON public.crm_ai_cursors(last_evaluated_at,last_evaluated_message_at);
CREATE TABLE IF NOT EXISTS public.crm_ai_scheduler_runs (id uuid PRIMARY KEY,invocation_source text NOT NULL DEFAULT 'scheduled_6h',started_at timestamptz NOT NULL DEFAULT now(),completed_at timestamptz,status text NOT NULL DEFAULT 'running' CHECK(status IN ('running','completed','partial','failed')),leads_considered integer NOT NULL DEFAULT 0,leads_selected integer NOT NULL DEFAULT 0,leads_skipped integer NOT NULL DEFAULT 0,deterministic_updates integer NOT NULL DEFAULT 0,ai_triggered integer NOT NULL DEFAULT 0,ai_completed integer NOT NULL DEFAULT 0,ai_failed integer NOT NULL DEFAULT 0,error_summary text,details jsonb NOT NULL DEFAULT '{}'::jsonb);
CREATE INDEX IF NOT EXISTS crm_ai_scheduler_runs_started_idx ON public.crm_ai_scheduler_runs(started_at DESC);
ALTER TABLE public.crm_ai_scheduler_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.crm_ai_scheduler_runs FROM PUBLIC,anon,authenticated;
DO $$ BEGIN IF EXISTS(SELECT 1 FROM cron.job WHERE jobname='crm_ai_scheduler_6h') THEN PERFORM cron.unschedule((SELECT jobid FROM cron.job WHERE jobname='crm_ai_scheduler_6h' LIMIT 1)); END IF; END $$;
CREATE OR REPLACE FUNCTION public.crm_invoke_ai_scheduler() RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path TO '' AS $$
DECLARE endpoint text;secret_value text;body_text text:='{"invocation_source":"scheduled_6h","limit":4}';timestamp_text text;signature_text text;request_id bigint;
BEGIN
 SELECT decrypted_secret INTO endpoint FROM vault.decrypted_secrets WHERE name='crm_api_url' LIMIT 1;
 SELECT decrypted_secret INTO secret_value FROM vault.decrypted_secrets WHERE name='crm_ai_scheduler_secret' LIMIT 1;
 IF endpoint IS NULL OR secret_value IS NULL THEN RAISE EXCEPTION 'CRM AI scheduler secrets are not configured'; END IF;
 timestamp_text:=extract(epoch FROM clock_timestamp())::bigint::text;signature_text:=encode(hmac(timestamp_text||'.'||body_text,secret_value,'sha256'),'hex');
 SELECT net.http_post(url:=rtrim(endpoint,'/')||'/api/internal/ai/scheduler',headers:=jsonb_build_object('Content-Type','application/json','X-EFPS-CRON-TIMESTAMP',timestamp_text,'X-EFPS-CRON-SIGNATURE',signature_text),body:=body_text::jsonb,timeout_milliseconds:=300000) INTO request_id;
 RETURN request_id;
END; $$;
REVOKE ALL ON FUNCTION public.crm_invoke_ai_scheduler() FROM PUBLIC;GRANT EXECUTE ON FUNCTION public.crm_invoke_ai_scheduler() TO postgres;
SELECT cron.schedule('crm_ai_scheduler_6h','0 */6 * * *','select public.crm_invoke_ai_scheduler();');
COMMIT;
