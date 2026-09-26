# Canonical Housing Sheet → CRM inventory mirror

**Source:** `Housing_Listings` tab in the Housing Listings Google Sheet. The legacy Slack flow still writes this sheet; the new CRM sync uses no AWS resources. CRM never writes back to the sheet.

**Implementation:** `src/housing-sheet-adapter.mjs` (read-only OAuth scope), `src/inventory-sync.mjs` (full snapshot, row hashes, transaction, advisory lock, tombstones), `crm-server.mjs` (signed sync endpoint, protected matching API), `src/main.jsx` (live inventory browser view and 60-second refresh). `004_crm_inventory_sync_metadata.sql` and Supabase `crm_inventory_sync_tick()` support the mirror.

**Current gate:** the Supabase Vault secret named `crm_inventory_sync_hmac` is missing. The five-minute cron job `crm_inventory_sheet_reconcile_5m` was unscheduled pending that secret. Render's `CRM_INVENTORY_SYNC_SECRET` already exists, but its value is intentionally not disclosed. Set one newly generated identical HMAC secret in both Render and Supabase Vault using secure settings, then schedule `SELECT cron.schedule('crm_inventory_sheet_reconcile_5m','*/5 * * * *','SELECT public.crm_inventory_sync_tick();');` and run `SELECT public.crm_inventory_sync_tick();` once. Never commit secrets.

**Proof required before production sign-off:** a sync run recorded in `crm_inventory_sync_runs`; create a clearly labeled disposable property in the Sheet and verify `listing_id` and source hash in Supabase; edit a harmless field and verify hash/value change; delete the disposable Sheet row and verify `deleted_at` tombstone; restore/remove test records according to retention policy; authenticate into the deployed UI and verify the property and changes in Inventory. A live Sheet edit cannot be claimed propagated merely because the same data was manually inserted into Supabase.

**Safety:** never mark the entire inventory deleted if a Sheet read is empty. Duplicate listing IDs abort the sync. Raw WhatsApp messages and contact links participate in the hash but are not copied into CRM source records. `main` is read-only and must not be changed.
