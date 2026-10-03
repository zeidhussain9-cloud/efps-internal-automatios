BEGIN;

ALTER TABLE public.crm_contact_classifications
  DROP CONSTRAINT IF EXISTS crm_contact_classifications_classification_source_check;

ALTER TABLE public.crm_contact_classifications
  ADD CONSTRAINT crm_contact_classifications_classification_source_check
  CHECK (classification_source IN ('historical_extract','webhook_rule','operator','ai','deterministic_rule','pending'));

ALTER TABLE public.crm_contact_classifications
  ADD COLUMN IF NOT EXISTS deterministic_last_evaluated_at timestamptz,
  ADD COLUMN IF NOT EXISTS deterministic_last_evaluated_message_id bigint,
  ADD COLUMN IF NOT EXISTS deterministic_last_evaluated_message_at timestamptz,
  ADD COLUMN IF NOT EXISTS deterministic_rule_version text;

CREATE INDEX IF NOT EXISTS crm_contact_classifications_deterministic_queue_idx
  ON public.crm_contact_classifications(source_number,status,last_seen_at DESC,deterministic_last_evaluated_at);

ALTER TABLE public.crm_leads
  ADD COLUMN IF NOT EXISTS auto_qualified boolean NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS crm_leads_auto_qualified_idx
  ON public.crm_leads(auto_qualified,updated_at DESC);

CREATE TABLE IF NOT EXISTS public.crm_deterministic_scheduler_runs (
  id uuid PRIMARY KEY,
  invocation_source text NOT NULL DEFAULT 'scheduled_1h',
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  status text NOT NULL DEFAULT 'running'
    CHECK(status IN ('running','completed','partial','failed','dry_run')),
  candidates_considered integer NOT NULL DEFAULT 0,
  qualified_count integer NOT NULL DEFAULT 0,
  unqualified_count integer NOT NULL DEFAULT 0,
  pending_count integer NOT NULL DEFAULT 0,
  skipped_count integer NOT NULL DEFAULT 0,
  failed_count integer NOT NULL DEFAULT 0,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  error_summary text
);

CREATE INDEX IF NOT EXISTS crm_deterministic_scheduler_runs_started_idx
  ON public.crm_deterministic_scheduler_runs(started_at DESC);

ALTER TABLE public.crm_deterministic_scheduler_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.crm_deterministic_scheduler_runs FROM PUBLIC,anon,authenticated;

COMMIT;