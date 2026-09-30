-- CRM two-layer qualification gate v1
-- Layer 0: append every WhAPI event.
-- Layer 1: classify contact identity/type.
-- Layer 2: only qualified contacts become crm_leads.
-- Layer 3: lead_type tracks follow-up state independently.
BEGIN;

CREATE TABLE IF NOT EXISTS public.crm_contact_classifications (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_number text NOT NULL,
  phone text NOT NULL,
  classification_code text NOT NULL DEFAULT 'pending'
    CHECK (classification_code IN (
      'pending','qualified_lead','personal_family','agent_partner','business',
      'promotion','vendor_supplier','internal','cold_inquiry','property_listing_sent','unknown'
    )),
  classification_label text NOT NULL DEFAULT 'Pending classification',
  classification_source text NOT NULL DEFAULT 'pending'
    CHECK (classification_source IN ('historical_extract','webhook_rule','operator','ai','pending')),
  confidence numeric(5,4) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','classified','promoted','excluded')),
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  classified_at timestamptz,
  promoted_at timestamptz,
  lead_id text REFERENCES public.crm_leads(id),
  UNIQUE (source_number, phone)
);
CREATE INDEX IF NOT EXISTS crm_contact_classifications_status_idx
  ON public.crm_contact_classifications(status,last_seen_at DESC);
CREATE INDEX IF NOT EXISTS crm_contact_classifications_code_idx
  ON public.crm_contact_classifications(classification_code,last_seen_at DESC);
ALTER TABLE public.crm_contact_classifications ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.crm_contact_classifications FROM anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON public.crm_contact_classifications TO service_role;

ALTER TABLE public.crm_messages ALTER COLUMN lead_id DROP NOT NULL;
ALTER TABLE public.crm_messages ADD COLUMN IF NOT EXISTS classification_id bigint REFERENCES public.crm_contact_classifications(id);
CREATE INDEX IF NOT EXISTS crm_messages_classification_idx
  ON public.crm_messages(classification_id,message_at ASC,id ASC);

ALTER TABLE public.crm_leads ADD COLUMN IF NOT EXISTS classification_id bigint REFERENCES public.crm_contact_classifications(id);
ALTER TABLE public.crm_leads ADD COLUMN IF NOT EXISTS lead_type text NOT NULL DEFAULT 'New';
ALTER TABLE public.crm_leads DROP CONSTRAINT IF EXISTS crm_leads_lead_type_check;
ALTER TABLE public.crm_leads ADD CONSTRAINT crm_leads_lead_type_check
  CHECK (lead_type IN ('New','Active Follow-up','Waiting on Customer','Waiting on Us','Nurture','Dormant','Converted','Lost','On Hold'));
CREATE INDEX IF NOT EXISTS crm_leads_lead_type_idx ON public.crm_leads(lead_type,updated_at DESC);

ALTER TABLE public.crm_webhook_events ADD COLUMN IF NOT EXISTS event_type text NOT NULL DEFAULT 'unknown';
ALTER TABLE public.crm_webhook_events ADD COLUMN IF NOT EXISTS event_fingerprint text;
ALTER TABLE public.crm_webhook_events ALTER COLUMN provider_event_id DROP NOT NULL;
UPDATE public.crm_webhook_events
SET event_fingerprint = encode(extensions.digest(payload::text || ':' || received_at::text,'sha256'),'hex')
WHERE event_fingerprint IS NULL;
ALTER TABLE public.crm_webhook_events ALTER COLUMN event_fingerprint SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS crm_webhook_events_fingerprint_idx
  ON public.crm_webhook_events(provider,event_fingerprint);

CREATE OR REPLACE FUNCTION public.crm_contact_classification_label(p_code text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
SELECT CASE p_code
WHEN 'qualified_lead' THEN 'Qualified Lead'
WHEN 'personal_family' THEN 'Personal / Family'
WHEN 'agent_partner' THEN 'Agent / Partner'
WHEN 'business' THEN 'Business'
WHEN 'promotion' THEN 'Promotion / Marketing'
WHEN 'vendor_supplier' THEN 'Vendor / Supplier'
WHEN 'internal' THEN 'Internal'
WHEN 'cold_inquiry' THEN 'Cold Inquiry'
WHEN 'property_listing_sent' THEN 'Property Listing Sent'
WHEN 'unknown' THEN 'Unclassified / Unknown'
ELSE 'Pending classification' END
$$;

CREATE OR REPLACE FUNCTION public.crm_normalize_classification(p_value text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
SELECT CASE lower(trim(coalesce(p_value,'')))
WHEN 'qualified lead' THEN 'qualified_lead'
WHEN 'personal/family' THEN 'personal_family'
WHEN 'personal / family' THEN 'personal_family'
WHEN 'agent/partner' THEN 'agent_partner'
WHEN 'agent / partner' THEN 'agent_partner'
WHEN 'spam/marketing' THEN 'promotion'
WHEN 'spam / marketing' THEN 'promotion'
WHEN 'promotion' THEN 'promotion'
WHEN 'business' THEN 'business'
WHEN 'vendor/supplier' THEN 'vendor_supplier'
WHEN 'vendor / supplier' THEN 'vendor_supplier'
WHEN 'internal' THEN 'internal'
WHEN 'cold inquiry' THEN 'cold_inquiry'
WHEN 'property listing sent' THEN 'property_listing_sent'
ELSE 'unknown' END
$$;

CREATE OR REPLACE FUNCTION public.crm_classify_live_text(p_body text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
SELECT CASE
WHEN coalesce(p_body,'') ~* '(unsubscribe|stop|offer|discount|sale|promotion|advertis|loan|insurance|credit card)' THEN 'promotion'
WHEN coalesce(p_body,'') ~* '(agent|broker|property dealer|realtor|channel partner)' THEN 'agent_partner'
WHEN coalesce(p_body,'') ~* '(vendor|supplier|maintenance|plumber|electrician|carpenter)' THEN 'vendor_supplier'
WHEN coalesce(p_body,'') ~* '(rent|rental|flat|apartment|room|house|villa|bhk|bedroom|property|move.?in|deposit|budget|location|locality)' THEN 'qualified_lead'
ELSE 'pending' END
$$;

-- This migration intentionally does not promote or delete historical leads.
-- Existing historical classification must be reconciled from the authoritative
-- source extract before the 228 imported records are changed.

COMMIT;