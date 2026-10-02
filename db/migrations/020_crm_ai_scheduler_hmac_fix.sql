BEGIN;
CREATE OR REPLACE FUNCTION public.crm_invoke_ai_scheduler()
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $$
DECLARE endpoint text;secret_value text;body_text text:='{"invocation_source":"scheduled_6h","limit":4}';timestamp_text text;signature_text text;request_id bigint;
BEGIN
 SELECT decrypted_secret INTO endpoint FROM vault.decrypted_secrets WHERE name='crm_api_url' LIMIT 1;
 SELECT decrypted_secret INTO secret_value FROM vault.decrypted_secrets WHERE name='crm_ai_scheduler_secret' LIMIT 1;
 IF endpoint IS NULL OR secret_value IS NULL THEN RAISE EXCEPTION 'CRM AI scheduler secrets are not configured'; END IF;
 timestamp_text:=extract(epoch FROM clock_timestamp())::bigint::text;
 signature_text:=encode(extensions.hmac(timestamp_text||'.'||body_text,secret_value,'sha256'),'hex');
 SELECT net.http_post(url:=rtrim(endpoint,'/')||'/api/internal/ai/scheduler',headers:=jsonb_build_object('Content-Type','application/json','X-EFPS-CRON-TIMESTAMP',timestamp_text,'X-EFPS-CRON-SIGNATURE',signature_text),body:=body_text::jsonb,timeout_milliseconds:=300000) INTO request_id;
 RETURN request_id;
END; $$;
REVOKE EXECUTE ON FUNCTION public.crm_invoke_ai_scheduler() FROM PUBLIC,anon,authenticated,service_role;
GRANT EXECUTE ON FUNCTION public.crm_invoke_ai_scheduler() TO postgres;
COMMIT;