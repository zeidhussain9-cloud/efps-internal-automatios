-- STAGED ONLY. Apply only after backups and final pre-cutover review.
-- Additive: v4 writer behavior remains unchanged until its compatibility release.
BEGIN;
CREATE OR REPLACE FUNCTION public.inventory_v5_valid_channels(channels text[])
RETURNS boolean LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
SET search_path = pg_catalog AS $$
 SELECT channels <@ ARRAY['Meta Catalogue','WhatsApp Group','Housing.com']::text[]
   AND array_position(channels,NULL) IS NULL
   AND cardinality(channels) = (SELECT count(DISTINCT c) FROM unnest(channels) c)
$$;
ALTER TABLE public.crm_inventory_snapshot
  ADD COLUMN IF NOT EXISTS availability text,
  ADD COLUMN IF NOT EXISTS pipeline_status text,
  ADD COLUMN IF NOT EXISTS live_on text[],
  ADD COLUMN IF NOT EXISTS onboarded_at timestamptz,
  ADD COLUMN IF NOT EXISTS inventory_contract_version integer NOT NULL DEFAULT 4;
-- NULL = not migrated; an empty channel array is a real migrated value.
ALTER TABLE public.crm_inventory_snapshot
  ADD CONSTRAINT inventory_v5_availability CHECK (
    availability IS NULL OR availability IN ('Available','On Hold','Rented Out')),
  ADD CONSTRAINT inventory_v5_pipeline CHECK (
    pipeline_status IS NULL OR pipeline_status IN ('Needs Review','Processing','Ready to Post','Removed')),
  ADD CONSTRAINT inventory_v5_channels CHECK (
    live_on IS NULL OR public.inventory_v5_valid_channels(live_on)),
  ADD CONSTRAINT inventory_v5_complete CHECK (
    inventory_contract_version = 4 OR
    (inventory_contract_version = 5 AND availability IS NOT NULL
     AND pipeline_status IS NOT NULL AND live_on IS NOT NULL));

CREATE TABLE public.inventory_field_provenance (
 listing_id text NOT NULL,
 field_name text NOT NULL,
 origin text NOT NULL CHECK(origin IN ('source_explicit','derived','manual','legacy_unknown')),
 source_reference text,
 evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
 inputs_hash text,
 derivation_version integer,
 last_generated_value jsonb,
 revision bigint NOT NULL DEFAULT 0 CHECK(revision >= 0),
 updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(listing_id,field_name)
);
CREATE TABLE public.inventory_processing_revisions (
 listing_id text PRIMARY KEY,
 current_input_hash text,
 last_acknowledged_values jsonb NOT NULL DEFAULT '{}'::jsonb,
 expected_self_write jsonb,
 pending_patch jsonb,
 revision bigint NOT NULL DEFAULT 0 CHECK(revision >= 0),
 lease_token uuid,
 lease_until timestamptz,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.inventory_reference_order (
 page_id uuid PRIMARY KEY,
 listing_id text NOT NULL UNIQUE,
 insertion_sequence bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
 active boolean NOT NULL DEFAULT true,
 seeded_rank integer CHECK(seeded_rank IS NULL OR seeded_rank > 0),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.inventory_renumber_jobs (
 job_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 membership_hash text NOT NULL,
 ordered_page_ids uuid[] NOT NULL,
 next_offset integer NOT NULL DEFAULT 0 CHECK(next_offset >= 0),
 status text NOT NULL CHECK(status IN ('pending','running','completed','failed','superseded')),
 error text,
 lease_token uuid,
 lease_until timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
-- Exactly one active renumber pass. Inserts during a pass coalesce into the
-- next membership snapshot rather than each launching an independent writer.
CREATE UNIQUE INDEX inventory_one_renumber_writer
 ON public.inventory_renumber_jobs ((true)) WHERE status = 'running';
ALTER TABLE public.inventory_field_provenance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_processing_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_reference_order ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_renumber_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_field_provenance, public.inventory_processing_revisions,
 public.inventory_reference_order, public.inventory_renumber_jobs FROM anon,authenticated;
GRANT ALL ON public.inventory_field_provenance, public.inventory_processing_revisions,
 public.inventory_reference_order, public.inventory_renumber_jobs TO service_role;
GRANT USAGE,SELECT ON SEQUENCE public.inventory_reference_order_insertion_sequence_seq,
 public.inventory_renumber_jobs_job_id_seq TO service_role;
COMMIT;
