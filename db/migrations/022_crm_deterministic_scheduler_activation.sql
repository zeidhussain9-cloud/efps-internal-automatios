BEGIN;

CREATE OR REPLACE FUNCTION public.crm_invoke_deterministic_scheduler()
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $$
DECLARE
  endpoint text;
  secret_value text;
  body_text text := '{"invocation_source":"scheduled_1h","limit":500,"dry_run":false}';
  timestamp_text text;
  signature_text text;
  request_id bigint;
BEGIN
  SELECT decrypted_secret INTO endpoint
  FROM vault.decrypted_secrets
  WHERE name='crm_api_url'
  LIMIT 1;

  SELECT decrypted_secret INTO secret_value
  FROM vault.decrypted_secrets
  WHERE name='crm_deterministic_scheduler_secret'
  LIMIT 1;

  IF endpoint IS NULL OR secret_value IS NULL THEN
    RAISE EXCEPTION 'Deterministic scheduler secrets are not configured';
  END IF;

  SELECT net.http_post(
    url:=rtrim(endpoint,'/')||'/api/internal/deterministic/scheduler',
    headers:=jsonb_build_object(
      'Content-Type','application/json',
      'X-EFPS-DETERMINISTIC-SECRET',secret_value
    ),
    body:=body_text::jsonb,
    timeout_milliseconds:=300000
  ) INTO request_id;

  RETURN request_id;
END;
$$;

REVOKE ALL ON FUNCTION public.crm_invoke_deterministic_scheduler() FROM PUBLIC,anon,authenticated,service_role;
GRANT EXECUTE ON FUNCTION public.crm_invoke_deterministic_scheduler() TO postgres;

DO $$
BEGIN
  IF EXISTS(SELECT 1 FROM cron.job WHERE jobname='crm_deterministic_scheduler_1h') THEN
    PERFORM cron.unschedule((SELECT jobid FROM cron.job WHERE jobname='crm_deterministic_scheduler_1h' LIMIT 1));
  END IF;
END $$;

SELECT cron.schedule(
  'crm_deterministic_scheduler_1h',
  '0 * * * *',
  'select public.crm_invoke_deterministic_scheduler();'
);

INSERT INTO public.crm_schema_migrations(version) VALUES(22) ON CONFLICT DO NOTHING;

COMMIT;