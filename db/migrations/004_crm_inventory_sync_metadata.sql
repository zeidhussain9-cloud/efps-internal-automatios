ALTER TABLE public.crm_inventory_snapshot ADD COLUMN IF NOT EXISTS source_record jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE public.crm_inventory_snapshot ADD COLUMN IF NOT EXISTS source_hash text;
ALTER TABLE public.crm_inventory_snapshot ADD COLUMN IF NOT EXISTS deleted_at timestamptz;
ALTER TABLE public.crm_inventory_snapshot ADD COLUMN IF NOT EXISTS last_synced_at timestamptz;
CREATE TABLE IF NOT EXISTS public.crm_inventory_sync_runs(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 run_id text NOT NULL UNIQUE,
 source_kind text NOT NULL,
 row_count integer NOT NULL,
 changed_count integer NOT NULL,
 removed_count integer NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.crm_inventory_sync_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.crm_inventory_sync_runs FROM anon,authenticated;
CREATE OR REPLACE VIEW public.crm_lead_inventory_matches WITH (security_invoker=true) AS
SELECT l.id AS lead_id,i.listing_id,i.locality,i.society_name,i.bhk,i.monthly_rent,i.listing_state,
(i.bhk=coalesce(l.requirements->>'bhk','')) AS bhk_match,
(i.monthly_rent<=NULLIF(l.requirements->>'budget','')::numeric) AS within_budget, i.furnishing,i.cloudinary_image_urls
FROM public.crm_leads l JOIN public.crm_inventory_snapshot i ON i.listing_state='Available' AND i.deleted_at IS NULL
WHERE l.id LIKE 'L-TEST-INV-%' AND i.bhk=coalesce(l.requirements->>'bhk','')
AND i.monthly_rent<=NULLIF(l.requirements->>'budget','')::numeric;
REVOKE ALL ON public.crm_lead_inventory_matches FROM anon,authenticated;
