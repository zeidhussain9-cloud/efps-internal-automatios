-- EasyFind CRM schema v1. PostgreSQL 15+. Apply through an explicit, reviewed migration.
-- CRM is the sole writer for lead data; inventory remains read-only in Google Sheets.
BEGIN;
CREATE TABLE IF NOT EXISTS crm_schema_migrations(version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS crm_leads(
 id text PRIMARY KEY,
 display_name text,
 normalized_phone text,
 status text NOT NULL DEFAULT 'Review',
 priority text NOT NULL DEFAULT 'Medium',
 requirements jsonb NOT NULL DEFAULT '{}'::jsonb,
 operator_notes text NOT NULL DEFAULT '',
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT crm_lead_status CHECK(status IN ('New','Qualified','Contacted','Follow-up','Review','Archived')),
 CONSTRAINT crm_lead_priority CHECK(priority IN ('High','Medium','Low'))
);
CREATE TABLE IF NOT EXISTS crm_lead_sources(
 lead_id text NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
 source_number text NOT NULL,
 source_contact_id text NOT NULL DEFAULT '',
 PRIMARY KEY(lead_id,source_number,source_contact_id)
);
CREATE TABLE IF NOT EXISTS crm_messages(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 lead_id text NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
 source_number text NOT NULL,
 provider_message_id text NOT NULL,
 direction text NOT NULL CHECK(direction IN ('Incoming','Outgoing')),
 message_type text NOT NULL DEFAULT 'text',
 body text,
 message_at timestamptz NOT NULL,
 imported_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(source_number,provider_message_id)
);
CREATE INDEX IF NOT EXISTS crm_messages_lead_at_idx ON crm_messages(lead_id,message_at,id);
CREATE TABLE IF NOT EXISTS crm_followups(
 id uuid PRIMARY KEY,
 lead_id text NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
 due_at timestamptz NOT NULL,
 note text NOT NULL DEFAULT '',
 completed_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS crm_followups_due_idx ON crm_followups(due_at) WHERE completed_at IS NULL;
CREATE TABLE IF NOT EXISTS crm_activity(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 lead_id text REFERENCES crm_leads(id) ON DELETE RESTRICT,
 actor text NOT NULL,
 action text NOT NULL,
 details jsonb NOT NULL DEFAULT '{}'::jsonb,
 occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS crm_activity_lead_at_idx ON crm_activity(lead_id,occurred_at DESC,id DESC);
CREATE TABLE IF NOT EXISTS crm_ai_runs(
 id uuid PRIMARY KEY,
 lead_id text NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
 model_name text NOT NULL,
 status text NOT NULL CHECK(status IN ('proposed','accepted','rejected','failed')),
 proposal jsonb,
 error_code text,
 created_at timestamptz NOT NULL DEFAULT now(),
 decided_at timestamptz
);
CREATE TABLE IF NOT EXISTS crm_drafts(
 id uuid PRIMARY KEY,
 lead_id text NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
 version integer NOT NULL CHECK(version>0),
 body text NOT NULL,
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','copied','opened','confirmed_sent')),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(lead_id,version)
);
CREATE TABLE IF NOT EXISTS crm_property_actions(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 lead_id text NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
 listing_id text NOT NULL,
 action text NOT NULL CHECK(action IN ('pinned','unpinned','excluded','unexcluded','suggested','shared','rejected','visited')),
 reason text NOT NULL DEFAULT '',
 actor text NOT NULL,
 occurred_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO crm_schema_migrations(version) VALUES(1) ON CONFLICT DO NOTHING;
-- Supabase server-only access: API roles have no grants or RLS policies.
ALTER TABLE crm_schema_migrations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_schema_migrations FROM anon, authenticated;
ALTER TABLE crm_leads ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_leads FROM anon, authenticated;
ALTER TABLE crm_lead_sources ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_lead_sources FROM anon, authenticated;
ALTER TABLE crm_messages ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_messages FROM anon, authenticated;
ALTER TABLE crm_followups ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_followups FROM anon, authenticated;
ALTER TABLE crm_activity ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_activity FROM anon, authenticated;
ALTER TABLE crm_ai_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_ai_runs FROM anon, authenticated;
ALTER TABLE crm_drafts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_drafts FROM anon, authenticated;
ALTER TABLE crm_property_actions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_property_actions FROM anon, authenticated;
COMMIT;
