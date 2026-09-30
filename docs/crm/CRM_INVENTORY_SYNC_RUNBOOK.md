# Canonical Housing Sheet → CRM inventory mirror

**Source:** `Housing_Listings` tab in the Housing Listings Google Sheet. The legacy Slack flow still writes this sheet; the new CRM sync uses no AWS resources. CRM never writes back to the sheet.

**Implementation:** `src/housing-sheet-adapter.mjs` (read-only OAuth scope), `src/inventory-sync.mjs` (full snapshot, row hashes, transaction, advisory lock, tombstones), `crm-server.mjs` (signed sync endpoint, protected matching API), `src/main.jsx` (live inventory browser view and 60-second refresh). `004_crm_inventory_sync_metadata.sql` and Supabase `crm_inventory_sync_tick()` support the mirror.

**Current state (2026-10-01):** the Supabase Vault secret `crm_inventory_sync_hmac` exists, Render's `CRM_INVENTORY_SYNC_SECRET` is configured, and the five-minute cron job `crm_inventory_sheet_reconcile_5m` is active. The latest five recorded syncs each fetched 81 rows with `changed_count=0` and `removed_count=0`, confirming scheduled Sheet-to-CRM reconciliation is running. Secret values are intentionally never disclosed or committed.

**Remaining proof for full inventory sign-off:** a controlled disposable Sheet add/edit/delete round trip must still be executed to prove mutation propagation and tombstoning. The scheduler itself is now active and producing successful sync records. A live Sheet edit cannot be claimed propagated merely because the same data was manually inserted into Supabase.

**Safety:** never mark the entire inventory deleted if a Sheet read is empty. Duplicate listing IDs abort the sync. Raw WhatsApp messages and contact links participate in the hash but are not copied into CRM source records. `main` is read-only and must not be changed.

## 2026-09-27 inventory UI correction
- Replaced the four synthetic Inventory examples with the full authenticated Supabase inventory overview, including both Available and Rented Out rows, a status/BHK/locality filter, property-detail modal, Cloudinary photo carousel, reconciliation arithmetic and last successful sync timestamp. No fabricated city/state values.
- Live Supabase audit at this checkpoint: 81 non-deleted rows = 65 Available + 16 Rented Out; 76 rows have at least one Cloudinary image URL (all 65 available listings). Five rented-out listings have no source photos. City/state source fields are blank on all 81 records, so the UI exposes locality and explicitly flags geographic fields as unrecorded. A sampled Cloudinary source image returned HTTP 200 with image/jpeg.
- Fix root cause: `imageUrls` only looked at the synthetic `photos` property; real database rows use `cloudinary_image_urls`. It now accepts both. `matchInventory` remains available-only for lead matching, while the new `/api/inventory/overview` includes all non-deleted rows for reconciliation.
- Code commit `72fc8fc` deployed live on Render; `b60c7ad` removes the duplicate mobile heading. 57 existing application tests plus a focused media test passed; local production build passed. A full authenticated production screenshot test and Sheet mutation round trip must still be independently verified before inventory is called fully production-ready.
