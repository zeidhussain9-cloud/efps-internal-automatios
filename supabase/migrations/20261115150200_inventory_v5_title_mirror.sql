-- STAGED ONLY. Title acknowledgment cannot leave its mirror behind.
BEGIN;
ALTER TABLE public.inventory_processing_revisions ADD COLUMN pending_title_mirror jsonb;
CREATE OR REPLACE FUNCTION public.inventory_v5_checked_title_mirror(p_page uuid,p_id text,p_revision bigint,p_values jsonb,p_same_revision boolean DEFAULT false)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE m public.crm_inventory_snapshot%ROWTYPE;
BEGIN
 SELECT * INTO m FROM public.crm_inventory_snapshot WHERE listing_id=p_id FOR UPDATE;
 -- Two explicit accepted states: bootstrap/title-ack rowN/mirrorN, or the
 -- established intake/dependency acknowledgment rowN/mirrorN-1. Never ahead.
 IF NOT FOUND OR m.inventory_contract_version IS DISTINCT FROM 5 OR m.deleted_at IS NOT NULL OR
  m.source_kind IS DISTINCT FROM 'housing_notion' OR m.source_tab IS DISTINCT FROM 'Housing Listings' OR
  m.inventory_revision IS NULL OR NOT(m.inventory_revision=p_revision OR (NOT p_same_revision AND m.inventory_revision=p_revision-1)) OR
  m.source_record->>'notion_page_id' IS DISTINCT FROM p_page::text OR m.source_record->>'listing_id' IS DISTINCT FROM p_id OR
  m.source_record->>'inventory_contract_version' IS DISTINCT FROM '5' OR
  p_values->>'Availability' IS NULL OR p_values->>'Pipeline Status' IS NULL OR jsonb_typeof(p_values->'Live On') IS DISTINCT FROM 'array' OR
  NOT(m.source_record @> (p_values-'_edited_at'-'_archived')) OR
  m.availability IS DISTINCT FROM p_values->>'Availability' OR m.listing_state IS DISTINCT FROM p_values->>'Availability' OR
  m.pipeline_status IS DISTINCT FROM p_values->>'Pipeline Status' OR m.business_status IS DISTINCT FROM p_values->>'Pipeline Status' OR
  to_jsonb(m.live_on) IS DISTINCT FROM p_values->'Live On' OR
  m.source_record->>'intake_conflict_quarantined'='true' OR m.source_record->>'identity_quarantined'='true' OR
  m.source_record->>'source_ack_conflict_quarantined'='true' THEN RAISE EXCEPTION 'Exact active title mirror baseline required'; END IF;
 RETURN to_jsonb(m);
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_checked_title_mirror FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_checked_title_mirror TO service_role;
COMMIT;
