create or replace function public.crm_reconcile_notion_inventory_event_listing_ids(
  p_source_page_ids text[],
  p_listing_ids text[]
) returns integer
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_updated integer := 0;
begin
  if coalesce(array_length(p_source_page_ids, 1), 0) < 1
     or coalesce(array_length(p_source_page_ids, 1), 0) > 500
     or coalesce(array_length(p_source_page_ids, 1), 0) <> coalesce(array_length(p_listing_ids, 1), 0) then
    raise exception 'invalid Notion inventory event listing ID mapping';
  end if;

  if exists (
    select 1 from unnest(p_source_page_ids) as ids(source_page_id)
    where source_page_id !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
  ) or exists (
    select 1 from unnest(p_listing_ids) as ids(listing_id)
    where listing_id !~ '^EF-[0-9]{4}-[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{4}$'
  ) then
    raise exception 'invalid Notion page or Listing ID';
  end if;

  update public.crm_inventory_intake_events as intake
  set listing_id = mapping.listing_id,
      updated_at = now()
  from unnest(p_source_page_ids, p_listing_ids) as mapping(source_page_id, listing_id)
  where intake.source_page_id = mapping.source_page_id
    and intake.listing_id is distinct from mapping.listing_id;

  get diagnostics v_updated = row_count;
  return v_updated;
end;
$$;

revoke all on function public.crm_reconcile_notion_inventory_event_listing_ids(text[], text[]) from public, anon, authenticated;
grant execute on function public.crm_reconcile_notion_inventory_event_listing_ids(text[], text[]) to service_role;
