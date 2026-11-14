-- Expose the operator/business review status as a first-class inventory projection field.
-- Preserve all existing source_record JSONB and intake_status semantics.
alter table public.crm_inventory_snapshot
  add column if not exists business_status text not null default 'Not recorded';

update public.crm_inventory_snapshot
set business_status = coalesce(nullif(btrim(source_record->>'status'), ''), 'Not recorded')
where business_status = 'Not recorded'
  and source_kind = 'housing_notion';

create index if not exists crm_inventory_snapshot_business_status_idx
  on public.crm_inventory_snapshot (business_status)
  where source_kind = 'housing_notion' and deleted_at is null;
