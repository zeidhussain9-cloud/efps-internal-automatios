-- STAGED ONLY. Database-enforced downgrade and revision fence, not a client read guard.
BEGIN;
ALTER TABLE public.crm_inventory_snapshot ADD COLUMN IF NOT EXISTS inventory_revision bigint;
CREATE OR REPLACE FUNCTION public.inventory_v5_snapshot_fence()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
BEGIN
 IF NEW.inventory_contract_version=5 THEN
  IF NEW.inventory_revision IS NULL OR NEW.inventory_revision<0 OR
   (NEW.source_record->>'inventory_contract_version')::integer IS DISTINCT FROM 5 THEN
   RAISE EXCEPTION 'Qualified inventory v5 revision required';
  END IF;
 END IF;
 IF TG_OP='UPDATE' AND OLD.inventory_contract_version=5 THEN
  IF NEW.inventory_contract_version IS DISTINCT FROM 5 THEN RAISE EXCEPTION 'Inventory contract downgrade rejected'; END IF;
  IF NEW.inventory_revision<OLD.inventory_revision THEN RAISE EXCEPTION 'Stale inventory revision rejected'; END IF;
  IF NEW.inventory_revision=OLD.inventory_revision AND
   (to_jsonb(NEW)-'last_synced_at'-'source_snapshot_at' IS DISTINCT FROM to_jsonb(OLD)-'last_synced_at'-'source_snapshot_at') THEN
   RAISE EXCEPTION 'Inventory revision reused for different content';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER inventory_v5_snapshot_fence BEFORE INSERT OR UPDATE ON public.crm_inventory_snapshot
 FOR EACH ROW EXECUTE FUNCTION public.inventory_v5_snapshot_fence();
CREATE OR REPLACE FUNCTION public.inventory_v5_sync_snapshot(p_snapshot jsonb,p_page_id uuid,p_lease uuid,p_revision bigint)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_processing_revisions%ROWTYPE;s public.crm_inventory_snapshot%ROWTYPE;
BEGIN
 SELECT * INTO r FROM public.inventory_processing_revisions WHERE page_id=p_page_id FOR UPDATE;
 IF NOT FOUND OR r.lease_token IS DISTINCT FROM p_lease OR r.lease_until<=clock_timestamp() OR r.revision IS DISTINCT FROM p_revision THEN
  RAISE EXCEPTION 'Stale mirror lease or revision';
 END IF;
 s=jsonb_populate_record(NULL::public.crm_inventory_snapshot,p_snapshot);
 IF s.source_record->>'notion_page_id' IS DISTINCT FROM p_page_id::text OR s.listing_id IS DISTINCT FROM r.listing_id OR s.inventory_contract_version IS DISTINCT FROM 5 OR s.inventory_revision IS DISTINCT FROM p_revision THEN
  RAISE EXCEPTION 'Mirror identity/version/revision mismatch';
 END IF;
 INSERT INTO public.crm_inventory_snapshot(listing_id,source_kind,source_tab,locality,society_name,bhk,monthly_rent,furnishing,
 listing_state,business_status,intake_status,pet_friendly,cloudinary_image_urls,source_snapshot_at,last_synced_at,
 source_record,source_hash,availability,pipeline_status,live_on,onboarded_at,inventory_contract_version,inventory_revision,deleted_at)
 VALUES(s.listing_id,s.source_kind,s.source_tab,s.locality,s.society_name,s.bhk,s.monthly_rent,s.furnishing,
 s.listing_state,s.business_status,s.intake_status,s.pet_friendly,s.cloudinary_image_urls,s.source_snapshot_at,s.last_synced_at,
 s.source_record,s.source_hash,s.availability,s.pipeline_status,s.live_on,s.onboarded_at,s.inventory_contract_version,s.inventory_revision,s.deleted_at)
 ON CONFLICT(listing_id) DO UPDATE SET source_kind=excluded.source_kind,source_tab=excluded.source_tab,locality=excluded.locality,
 society_name=excluded.society_name,bhk=excluded.bhk,monthly_rent=excluded.monthly_rent,furnishing=excluded.furnishing,
 listing_state=excluded.listing_state,business_status=excluded.business_status,intake_status=excluded.intake_status,
 pet_friendly=excluded.pet_friendly,cloudinary_image_urls=excluded.cloudinary_image_urls,source_snapshot_at=excluded.source_snapshot_at,
 last_synced_at=excluded.last_synced_at,source_record=excluded.source_record,source_hash=excluded.source_hash,
 availability=excluded.availability,pipeline_status=excluded.pipeline_status,live_on=excluded.live_on,onboarded_at=excluded.onboarded_at,
 inventory_contract_version=excluded.inventory_contract_version,inventory_revision=excluded.inventory_revision,deleted_at=excluded.deleted_at;
 RETURN jsonb_build_object('ok',true);
END $$;
CREATE OR REPLACE FUNCTION public.inventory_v5_quarantine_identity(p_page_id uuid,p_lease uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE r public.inventory_processing_revisions%ROWTYPE;s public.crm_inventory_snapshot%ROWTYPE;n bigint;
BEGIN
 SELECT * INTO r FROM public.inventory_processing_revisions WHERE page_id=p_page_id FOR UPDATE;
 IF NOT FOUND OR r.lease_token IS DISTINCT FROM p_lease OR r.lease_until<=clock_timestamp() THEN RAISE EXCEPTION 'Stale quarantine lease'; END IF;
 SELECT * INTO s FROM public.crm_inventory_snapshot WHERE listing_id=r.listing_id FOR UPDATE;
 IF NOT FOUND THEN RETURN jsonb_build_object('found',false,'revision',r.revision); END IF;
 IF s.source_record->>'notion_page_id' IS DISTINCT FROM p_page_id::text THEN RAISE EXCEPTION 'Known mirror page identity mismatch'; END IF;
 n=greatest(coalesce(s.inventory_revision,0),r.revision)+1;
 UPDATE public.crm_inventory_snapshot SET pipeline_status='Needs Review',business_status='Needs Review',
  source_record=source_record||jsonb_build_object('Pipeline Status','Needs Review','identity_quarantined',true),
  inventory_revision=n,last_synced_at=clock_timestamp() WHERE listing_id=r.listing_id;
 UPDATE public.inventory_processing_revisions SET revision=n,processing_status='needs_review' WHERE page_id=p_page_id;
 RETURN jsonb_build_object('found',true,'revision',n,'listing_id',r.listing_id);
END $$;
REVOKE ALL ON FUNCTION public.inventory_v5_quarantine_identity FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_quarantine_identity TO service_role;
REVOKE ALL ON FUNCTION public.inventory_v5_sync_snapshot FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.inventory_v5_sync_snapshot TO service_role;
COMMIT;
