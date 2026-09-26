-- Cover lead foreign keys reported by Supabase performance advisor.
CREATE INDEX IF NOT EXISTS crm_ai_runs_lead_idx ON public.crm_ai_runs(lead_id,created_at DESC);
CREATE INDEX IF NOT EXISTS crm_followups_lead_idx ON public.crm_followups(lead_id);
CREATE INDEX IF NOT EXISTS crm_property_actions_lead_idx ON public.crm_property_actions(lead_id,occurred_at DESC);
