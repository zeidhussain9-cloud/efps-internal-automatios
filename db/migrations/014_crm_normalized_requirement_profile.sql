-- CRM requirement profile v1: normalized, inventory-matchable, operator-editable lead requirements.
BEGIN;
CREATE TABLE IF NOT EXISTS public.crm_lead_requirements (
 lead_id text PRIMARY KEY REFERENCES public.crm_leads(id) ON DELETE RESTRICT,
 bhk text NOT NULL DEFAULT '',
 budget numeric(12,2),
 preferred_locations text[] NOT NULL DEFAULT '{}',
 tenant_type text NOT NULL DEFAULT 'Not specified',
 move_in_date date,
 pets text NOT NULL DEFAULT 'Unknown',
 veg_nonveg text NOT NULL DEFAULT 'Unknown',
 furnishing text NOT NULL DEFAULT 'Unknown',
 parking text NOT NULL DEFAULT 'Unknown',
 property_type text NOT NULL DEFAULT 'Any',
 bathrooms text NOT NULL DEFAULT '',
 occupancy_count integer,
 lease_term_months integer,
 preferred_floor text NOT NULL DEFAULT '',
 preferred_amenities text[] NOT NULL DEFAULT '{}',
 notes text NOT NULL DEFAULT '',
 updated_by text NOT NULL DEFAULT 'system',
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT crm_lead_requirements_pets_check CHECK(pets IN ('Yes','No','Unknown')),
 CONSTRAINT crm_lead_requirements_veg_check CHECK(veg_nonveg IN ('Veg','Non-Veg','No Preference','Unknown')),
 CONSTRAINT crm_lead_requirements_tenant_check CHECK(tenant_type IN ('Family','Bachelors','Couples','Students','Working Professionals','Corporate','Other','Not specified')),
 CONSTRAINT crm_lead_requirements_furnishing_check CHECK(furnishing IN ('Fully Furnished','Semi Furnished','Unfurnished','Any','Unknown')),
 CONSTRAINT crm_lead_requirements_parking_check CHECK(parking IN ('Required','Not Required','Any','Unknown')),
 CONSTRAINT crm_lead_requirements_budget_check CHECK(budget IS NULL OR budget >= 0),
 CONSTRAINT crm_lead_requirements_occupancy_check CHECK(occupancy_count IS NULL OR occupancy_count > 0),
 CONSTRAINT crm_lead_requirements_lease_check CHECK(lease_term_months IS NULL OR lease_term_months > 0)
);
CREATE INDEX IF NOT EXISTS crm_lead_requirements_bhk_budget_idx ON public.crm_lead_requirements(bhk,budget);
CREATE INDEX IF NOT EXISTS crm_lead_requirements_tenant_idx ON public.crm_lead_requirements(tenant_type);
ALTER TABLE public.crm_lead_requirements ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.crm_lead_requirements FROM anon,authenticated;
CREATE OR REPLACE FUNCTION public.crm_touch_lead_requirements_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at=now(); RETURN NEW; END $$;
DROP TRIGGER IF EXISTS crm_lead_requirements_touch ON public.crm_lead_requirements;
CREATE TRIGGER crm_lead_requirements_touch BEFORE UPDATE ON public.crm_lead_requirements FOR EACH ROW EXECUTE FUNCTION public.crm_touch_lead_requirements_updated_at();
INSERT INTO public.crm_lead_requirements(
 lead_id,bhk,budget,preferred_locations,tenant_type,move_in_date,pets,veg_nonveg,furnishing,parking,
 property_type,bathrooms,occupancy_count,lease_term_months,preferred_floor,preferred_amenities,notes,updated_by
)
SELECT
 l.id, COALESCE(l.requirements->>'bhk',''),
 NULLIF(regexp_replace(COALESCE(l.requirements->>'budget',''),'[^0-9.]','','g'),'')::numeric,
 CASE WHEN COALESCE(l.requirements->>'locality',l.requirements->>'preferred_location','')='' THEN '{}' ELSE ARRAY[COALESCE(l.requirements->>'locality',l.requirements->>'preferred_location','')] END,
 l.tenant_type,
 CASE WHEN (l.requirements->>'move_in_date') ~ '^\d{4}-\d{2}-\d{2}$' THEN (l.requirements->>'move_in_date')::date ELSE NULL END,
 CASE WHEN lower(COALESCE(l.requirements->>'pets',l.requirements->>'pet_preference','')) IN ('yes','true') THEN 'Yes' WHEN lower(COALESCE(l.requirements->>'pets',l.requirements->>'pet_preference','')) IN ('no','false') THEN 'No' ELSE 'Unknown' END,
 CASE WHEN lower(COALESCE(l.requirements->>'veg_nonveg','')) IN ('veg','vegetarian') THEN 'Veg' WHEN lower(COALESCE(l.requirements->>'veg_nonveg','')) IN ('non-veg','non veg','nonveg','nonvegetarian') THEN 'Non-Veg' WHEN lower(COALESCE(l.requirements->>'veg_nonveg','')) IN ('no preference','any') THEN 'No Preference' ELSE 'Unknown' END,
 CASE WHEN lower(COALESCE(l.requirements->>'furnishing','')) LIKE '%semi%' THEN 'Semi Furnished' WHEN lower(COALESCE(l.requirements->>'furnishing','')) LIKE '%fully%' THEN 'Fully Furnished' WHEN lower(COALESCE(l.requirements->>'furnishing','')) LIKE '%unfurn%' THEN 'Unfurnished' WHEN lower(COALESCE(l.requirements->>'furnishing','')) IN ('any','no preference') THEN 'Any' ELSE 'Unknown' END,
 CASE WHEN lower(COALESCE(l.requirements->>'parking','')) IN ('required','yes','true') THEN 'Required' WHEN lower(COALESCE(l.requirements->>'parking','')) IN ('not required','no','false') THEN 'Not Required' WHEN lower(COALESCE(l.requirements->>'parking','')) IN ('any','no preference') THEN 'Any' ELSE 'Unknown' END,
 COALESCE(NULLIF(l.requirements->>'property_type',''),'Any'), COALESCE(l.requirements->>'bathrooms',''),
 CASE WHEN COALESCE(l.requirements->>'occupancy_count','') ~ '^\d+$' THEN (l.requirements->>'occupancy_count')::integer ELSE NULL END,
 CASE WHEN COALESCE(l.requirements->>'lease_term_months','') ~ '^\d+$' THEN (l.requirements->>'lease_term_months')::integer ELSE NULL END,
 COALESCE(l.requirements->>'preferred_floor',''),
 CASE WHEN jsonb_typeof(l.requirements->'preferred_amenities')='array' THEN ARRAY(SELECT jsonb_array_elements_text(l.requirements->'preferred_amenities')) ELSE '{}' END,
 COALESCE(l.requirements->>'notes',''),'migration'
FROM public.crm_leads l ON CONFLICT(lead_id) DO NOTHING;
INSERT INTO public.crm_schema_migrations(version) VALUES(14) ON CONFLICT DO NOTHING;
COMMIT;
