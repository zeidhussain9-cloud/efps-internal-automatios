BEGIN;

ALTER TABLE public.crm_ai_runs ADD COLUMN IF NOT EXISTS input_tokens integer;
ALTER TABLE public.crm_ai_runs ADD COLUMN IF NOT EXISTS output_tokens integer;
ALTER TABLE public.crm_ai_runs ADD COLUMN IF NOT EXISTS total_tokens integer;
ALTER TABLE public.crm_ai_runs ADD COLUMN IF NOT EXISTS estimated_cost_usd numeric(12,8);
ALTER TABLE public.crm_ai_runs ADD COLUMN IF NOT EXISTS pricing_source text NOT NULL DEFAULT 'standard_public_rates';

CREATE INDEX IF NOT EXISTS crm_ai_runs_created_at_idx ON public.crm_ai_runs(created_at DESC);

INSERT INTO public.crm_schema_migrations(version) VALUES(18) ON CONFLICT DO NOTHING;

COMMIT;
