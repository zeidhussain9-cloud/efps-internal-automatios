-- CRM AI scheduler pause
-- Operational pause requested 2026-10-04.
-- The AI scheduler implementation remains available; only its pg_cron trigger is paused.
-- Re-enable by scheduling crm_invoke_ai_scheduler() at the approved cadence.

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'crm_ai_scheduler_6h') THEN
    PERFORM cron.unschedule((SELECT jobid FROM cron.job WHERE jobname = 'crm_ai_scheduler_6h' LIMIT 1));
  END IF;
END $$;

INSERT INTO public.crm_schema_migrations(version)
VALUES (23)
ON CONFLICT DO NOTHING;
