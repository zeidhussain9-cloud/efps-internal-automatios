# Canonical Housing Sheet → CRM inventory mirror

**Source:** `Housing_Listings` tab in the Housing Listings Google Sheet. The legacy Slack flow still writes this sheet; the new CRM sync uses no AWS resources. CRM never writes back to the sheet.

**Implementation:** `src/housing-sheet-adapter.mjs` (read-only OAuth scope), `src/inventory-sync.mjs` (full snapshot, row hashes, transaction, advisory lock, tombstones, field-level change history), `crm-server.mjs` (signed sync endpoint, protected matching API), `src/main.jsx` (live inventory browser view and 60-second refresh). `004_crm_inventory_sync_metadata.sql` and Supabase `crm_inventory_sync_tick()` support the mirror.

**P1–P5 hardening (2026-10-01):** webhook event lead linkage is reconciled during promotion; the webhook recovery job repairs message-backed received/processing states; AU/AV are explicitly excluded from the A:AT CRM projection; `crm_inventory_sync_changes` records future field-level inventory changes; and the repository has a disposable create/edit/delete regression without mutating the production Sheet.

**Current production state (2026-10-01 production-live audit):** The five-minute cron job `crm_inventory_sheet_reconcile_5m` is active. It has **1,336/1,336 successful executions and 0 failures** through `2026-10-01 12:10:00 UTC`. The current live Housing Sheet contains **88 unique listing IDs**. The latest scheduled sync and a manual production reconciliation tick both read **88 rows with 0 changes and 0 removals**. Recomputing the adapter's exact operational SHA-256 row hashes from the live Sheet A:AT projection produced aggregate `284f59900fdcfdbcc2c39e8a4cacdb993181b201435ad9f36744c80487330f99`, exactly matching the active Supabase `crm_inventory_snapshot` aggregate. Current active DB inventory is 88 rows with no missing hashes, timestamps, IDs, or key projection mismatches.

**Reserved-column observation from the same live audit:** AU `source_group` is blank on all 88 active rows, but AV `inventory_locked` contains `Yes` on **43** active rows. AV is reserved and outside the CRM A:AT sync boundary; these values must not be overwritten without an explicit ownership decision.

**Historical change ledger:** pre-P3 runs retain row counts/hashes but not prior row versions. From the 2026-10-01 hardening release onward, `crm_inventory_sync_changes` stores field-level old/new values, change type, listing ID, source hashes and sync-run ID.

**Production audit report:** `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.

**Controlled round-trip note:** The repository now tests disposable create/edit/delete projection and field-level history without touching production data. A real Sheet mutation is intentionally not performed because the CRM integration is read-only and must not write the canonical Housing Sheet.

**Safety:** never mark the entire inventory deleted if a Sheet read is empty. Duplicate listing IDs abort the sync. Raw WhatsApp messages and contact links participate in the hash but are not copied into CRM source records. `main` is read-only and must not be changed.

## 2026-09-27 inventory UI correction
- Replaced the four synthetic Inventory examples with the full authenticated Supabase inventory overview, including both Available and Rented Out rows, a status/BHK/locality filter, property-detail modal, Cloudinary photo carousel, reconciliation arithmetic and last successful sync timestamp. No fabricated city/state values.
- Live Supabase audit at this checkpoint: 81 non-deleted rows = 65 Available + 16 Rented Out; 76 rows have at least one Cloudinary image URL (all 65 available listings). Five rented-out listings have no source photos. City/state source fields are blank on all 81 records, so the UI exposes locality and explicitly flags geographic fields as unrecorded. A sampled Cloudinary source image returned HTTP 200 with image/jpeg.
- Fix root cause: `imageUrls` only looked at the synthetic `photos` property; real database rows use `cloudinary_image_urls`. It now accepts both. `matchInventory` remains available-only for lead matching, while the new `/api/inventory/overview` includes all non-deleted rows for reconciliation.
- Code commit `72fc8fc` deployed live on Render; `b60c7ad` removes the duplicate mobile heading. 57 existing application tests plus a focused media test passed; local production build passed. A full authenticated production screenshot test and Sheet mutation round trip must still be independently verified before inventory is called fully production-ready.
