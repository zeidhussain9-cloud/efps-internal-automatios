-- Add the operator-facing Out of Coverage Area lead state.
-- UI label: OOC
BEGIN;

ALTER TABLE public.crm_leads DROP CONSTRAINT IF EXISTS crm_leads_lead_type_check;
ALTER TABLE public.crm_leads ADD CONSTRAINT crm_leads_lead_type_check
  CHECK (lead_type IN (
    'New',
    'Active Follow-up',
    'Waiting on Customer',
    'Waiting on Us',
    'Nurture',
    'Dormant',
    'Converted',
    'Lost',
    'On Hold',
    'Out of Coverage Area'
  ));

INSERT INTO public.crm_schema_migrations(version)
VALUES (11)
ON CONFLICT (version) DO NOTHING;

COMMIT;
