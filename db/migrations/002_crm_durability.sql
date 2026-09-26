-- CRM durability v2: provider inbox, AI cursors, append-only requirement evidence and request idempotency.
BEGIN;
CREATE TABLE IF NOT EXISTS crm_provider_events(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 provider text NOT NULL,
 provider_event_id text NOT NULL,
 event_type text NOT NULL DEFAULT '',
 payload jsonb NOT NULL,
 received_at timestamptz NOT NULL DEFAULT now(),
 processed_at timestamptz,
 status text NOT NULL DEFAULT 'received' CHECK(status IN ('received','processing','processed','failed')),
 attempts integer NOT NULL DEFAULT 0 CHECK(attempts>=0),
 last_error text,
 UNIQUE(provider,provider_event_id)
);
CREATE INDEX IF NOT EXISTS crm_provider_events_status_idx ON crm_provider_events(status,received_at,id);

CREATE TABLE IF NOT EXISTS crm_ai_cursors(
 source_number text PRIMARY KEY,
 cursor text NOT NULL DEFAULT '',
 last_message_at timestamptz,
 updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS crm_requirement_evidence(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 lead_id text NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
 field_name text NOT NULL,
 value jsonb NOT NULL,
 source_message_id bigint REFERENCES crm_messages(id) ON DELETE RESTRICT,
 source_number text NOT NULL DEFAULT '',
 actor text NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS crm_requirement_evidence_lead_at_idx ON crm_requirement_evidence(lead_id,recorded_at DESC,id DESC);

CREATE TABLE IF NOT EXISTS crm_idempotency_keys(
 key text PRIMARY KEY,
 scope text NOT NULL,
 request_hash text NOT NULL,
 response jsonb,
 created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE crm_provider_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_provider_events FROM anon, authenticated;
ALTER TABLE crm_ai_cursors ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_ai_cursors FROM anon, authenticated;
ALTER TABLE crm_requirement_evidence ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_requirement_evidence FROM anon, authenticated;
ALTER TABLE crm_idempotency_keys ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_idempotency_keys FROM anon, authenticated;
COMMIT;