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

CREATE TABLE IF NOT EXISTS crm_property_media(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 listing_id text NOT NULL,
 media_url text NOT NULL CHECK(media_url LIKE 'https://res.cloudinary.com/%'),
 cloudinary_public_id text NOT NULL DEFAULT '',
 media_type text NOT NULL DEFAULT 'image' CHECK(media_type IN ('image','video')),
 sort_order integer NOT NULL DEFAULT 0 CHECK(sort_order>=0),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(listing_id,media_url)
);
CREATE INDEX IF NOT EXISTS crm_property_media_listing_idx ON crm_property_media(listing_id,sort_order,id);

ALTER TABLE crm_provider_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_provider_events FROM anon, authenticated;
ALTER TABLE crm_ai_cursors ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_ai_cursors FROM anon, authenticated;
ALTER TABLE crm_requirement_evidence ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_requirement_evidence FROM anon, authenticated;
ALTER TABLE crm_idempotency_keys ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_idempotency_keys FROM anon, authenticated;
ALTER TABLE crm_property_media ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE crm_property_media FROM anon, authenticated;
COMMIT;

CREATE OR REPLACE FUNCTION crm_reject_append_only_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
 RAISE EXCEPTION 'append-only CRM record cannot be modified';
END;
$$;

DROP TRIGGER IF EXISTS crm_messages_append_only ON crm_messages;
CREATE TRIGGER crm_messages_append_only BEFORE UPDATE OR DELETE ON crm_messages
FOR EACH ROW EXECUTE FUNCTION crm_reject_append_only_mutation();

DROP TRIGGER IF EXISTS crm_activity_append_only ON crm_activity;
CREATE TRIGGER crm_activity_append_only BEFORE UPDATE OR DELETE ON crm_activity
FOR EACH ROW EXECUTE FUNCTION crm_reject_append_only_mutation();

DROP TRIGGER IF EXISTS crm_requirement_evidence_append_only ON crm_requirement_evidence;
CREATE TRIGGER crm_requirement_evidence_append_only BEFORE UPDATE OR DELETE ON crm_requirement_evidence
FOR EACH ROW EXECUTE FUNCTION crm_reject_append_only_mutation();

DROP TRIGGER IF EXISTS crm_property_actions_append_only ON crm_property_actions;
CREATE TRIGGER crm_property_actions_append_only BEFORE UPDATE OR DELETE ON crm_property_actions
FOR EACH ROW EXECUTE FUNCTION crm_reject_append_only_mutation();

CREATE OR REPLACE FUNCTION crm_touch_lead_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
 NEW.updated_at=now();
 RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS crm_leads_touch_updated_at ON crm_leads;
CREATE TRIGGER crm_leads_touch_updated_at BEFORE UPDATE ON crm_leads
FOR EACH ROW EXECUTE FUNCTION crm_touch_lead_updated_at();
