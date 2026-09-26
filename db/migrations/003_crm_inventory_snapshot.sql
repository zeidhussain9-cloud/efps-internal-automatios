-- Inventory is a read-only, versioned snapshot of the Slack-owned Housing_Listings sheet.
-- Do not import contact links, raw messages, group links, or owner details.
CREATE TABLE IF NOT EXISTS public.crm_inventory_snapshot (
 listing_id text PRIMARY KEY,
 source_kind text NOT NULL CHECK(source_kind IN ('housing_sheet','synthetic')),
 source_tab text NOT NULL,
 locality text NOT NULL DEFAULT '',
 society_name text NOT NULL DEFAULT '',
 bhk text NOT NULL DEFAULT '',
 monthly_rent numeric(12,2),
 furnishing text NOT NULL DEFAULT '',
 listing_state text NOT NULL DEFAULT 'Unknown',
 intake_status text NOT NULL DEFAULT '',
 pet_friendly text NOT NULL DEFAULT '',
 cloudinary_image_urls jsonb NOT NULL DEFAULT '[]'::jsonb CHECK(jsonb_typeof(cloudinary_image_urls)='array'),
 source_snapshot_at timestamptz NOT NULL DEFAULT now(),
 imported_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.crm_inventory_snapshot ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.crm_inventory_snapshot FROM anon,authenticated;
CREATE INDEX IF NOT EXISTS crm_inventory_snapshot_lookup ON public.crm_inventory_snapshot(listing_state,bhk,monthly_rent);
CREATE OR REPLACE VIEW public.crm_lead_inventory_matches WITH (security_invoker=true) AS
SELECT l.id AS lead_id,i.listing_id,i.locality,i.society_name,i.bhk,i.monthly_rent,i.listing_state,
(i.bhk=coalesce(l.requirements->>'bhk','')) AS bhk_match,
(i.monthly_rent<=NULLIF(l.requirements->>'budget','')::numeric) AS within_budget
FROM public.crm_leads l JOIN public.crm_inventory_snapshot i ON i.listing_state='Available'
WHERE l.id LIKE 'L-TEST-INV-%' AND i.bhk=coalesce(l.requirements->>'bhk','')
AND i.monthly_rent<=NULLIF(l.requirements->>'budget','')::numeric;
REVOKE ALL ON public.crm_lead_inventory_matches FROM anon,authenticated;
