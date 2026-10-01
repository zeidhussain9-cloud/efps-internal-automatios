BEGIN;
ALTER TABLE crm_drafts ADD COLUMN IF NOT EXISTS ai_run_id uuid REFERENCES crm_ai_runs(id) ON DELETE SET NULL;
ALTER TABLE crm_drafts ADD COLUMN IF NOT EXISTS ai_provider text NOT NULL DEFAULT 'unknown';
ALTER TABLE crm_drafts ADD COLUMN IF NOT EXISTS model_name text NOT NULL DEFAULT 'unknown';
CREATE INDEX IF NOT EXISTS crm_drafts_ai_run_idx ON crm_drafts(ai_run_id);
UPDATE crm_drafts d
SET ai_run_id = x.id,
    model_name = x.model_name,
    ai_provider = CASE WHEN x.model_name LIKE 'au.%' OR x.model_name LIKE 'anthropic.%' THEN 'aws-bedrock' ELSE 'ollama' END
FROM LATERAL (
  SELECT r.id,r.model_name
  FROM crm_ai_runs r
  WHERE r.lead_id=d.lead_id AND r.created_at <= d.created_at
  ORDER BY r.created_at DESC,r.id DESC
  LIMIT 1
) x
WHERE d.ai_run_id IS NULL;
INSERT INTO public.crm_schema_migrations(version) VALUES(16) ON CONFLICT DO NOTHING;
COMMIT;
