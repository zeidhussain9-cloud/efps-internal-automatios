-- Notion Housing Listings is the canonical edit surface. The existing Sheet
-- snapshot remains as a compatibility source during the transition, while
-- Notion-owned rows take precedence for the same Listing ID.
ALTER TABLE public.crm_inventory_snapshot
  DROP CONSTRAINT IF EXISTS crm_inventory_snapshot_source_kind_check;

ALTER TABLE public.crm_inventory_snapshot
  ADD CONSTRAINT crm_inventory_snapshot_source_kind_check
  CHECK (source_kind IN ('housing_sheet', 'housing_notion', 'synthetic'));

CREATE OR REPLACE FUNCTION public.crm_allocate_notion_inventory_listing_id(
  p_source_page_id text
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_listing_id text;
  v_suffix text;
  v_alphabet constant text := '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
  v_i integer;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.crm_inventory_intake_events
    WHERE source_page_id = p_source_page_id
  ) THEN
    RAISE EXCEPTION 'Notion page must be claimed before allocating a Listing ID';
  END IF;

  PERFORM pg_advisory_xact_lock(104729, 82);
  SELECT listing_id INTO v_listing_id
  FROM public.crm_inventory_intake_events
  WHERE source_page_id = p_source_page_id
  FOR UPDATE;
  IF v_listing_id IS NOT NULL THEN
    RETURN v_listing_id;
  END IF;

  FOR attempt IN 1..100 LOOP
    v_suffix := '';
    FOR v_i IN 1..4 LOOP
      v_suffix := v_suffix || substr(v_alphabet, floor(random() * length(v_alphabet))::integer + 1, 1);
    END LOOP;
    v_listing_id := 'EF-' || to_char(now() AT TIME ZONE 'UTC', 'YYMM') || '-' || v_suffix;
    EXIT WHEN NOT EXISTS (
      SELECT 1 FROM public.crm_inventory_snapshot WHERE listing_id = v_listing_id
      UNION ALL
      SELECT 1 FROM public.crm_inventory_intake_events WHERE listing_id = v_listing_id
    );
    v_listing_id := NULL;
  END LOOP;

  IF v_listing_id IS NULL THEN
    RAISE EXCEPTION 'Unable to allocate a unique Listing ID';
  END IF;

  UPDATE public.crm_inventory_intake_events
  SET listing_id = v_listing_id, updated_at = now()
  WHERE source_page_id = p_source_page_id;
  RETURN v_listing_id;
END;
$$;

REVOKE ALL ON FUNCTION public.crm_allocate_notion_inventory_listing_id(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crm_allocate_notion_inventory_listing_id(text) TO service_role;
