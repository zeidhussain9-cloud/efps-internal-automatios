-- CRM historical classification and conversation provenance v3.
BEGIN;

ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS classification text;

UPDATE crm_leads
SET classification=COALESCE(
  NULLIF(requirements->'fields'->>'classification',''),
  NULLIF(requirements->>'classification','')
)
WHERE classification IS NULL;

CREATE INDEX IF NOT EXISTS crm_leads_classification_idx ON crm_leads(classification);

ALTER TABLE crm_messages ALTER COLUMN provider_message_id DROP NOT NULL;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS source_message_id text;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS sender_name text;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS media_urls jsonb;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS media_filenames jsonb;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS extracted_intent text;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS extracted_entities jsonb;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS sentiment text;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS requires_followup boolean NOT NULL DEFAULT false;
ALTER TABLE crm_messages ADD COLUMN IF NOT EXISTS replied_to_source_message_id text;

CREATE UNIQUE INDEX IF NOT EXISTS crm_messages_source_message_idx
ON crm_messages(source_number,source_message_id)
WHERE source_message_id IS NOT NULL;

ALTER TABLE crm_messages DROP CONSTRAINT IF EXISTS crm_messages_identity_check;
ALTER TABLE crm_messages ADD CONSTRAINT crm_messages_identity_check
CHECK (provider_message_id IS NOT NULL OR source_message_id IS NOT NULL);

COMMIT;
