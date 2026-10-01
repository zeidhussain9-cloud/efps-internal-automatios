# Canonical Housing Sheet → CRM inventory mirror

## Authoritative current verified state — 2026-10-01 21:55 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **CRM commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **CRM tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **main:** `b2fbf366021852aedd4bf0ec66484ad421fb5662`
- **main tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** `dep-dav82h3m8hqs7399j4ug` = **LIVE**
- **Live Render commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 186 leads; 6,870 messages; 465 webhook events; 310 classifications; 186 requirements; 196 AI runs; 196 drafts; 186 AI cursors; 88 active inventory rows.
- **Classification status:** 186 promoted; 88 classified; 23 pending; 13 excluded = 310 total.
- **Webhook status:** 465 processed; 0 received; 0 processing; 0 failed.
- **Message reconciliation:** 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 829/829 distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 76/76 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v8.
- **AWS legacy webhook:** no changes in the audited CRM hardening range.
- **24-item CRM audit:** GREEN / VERIFIED.

### Current operational flow

```text
WhAPI +919148338801
  -> crm_webhook_events (persist + deduplicate)
  -> webhook processor/reconciler
  -> crm_messages + classification registry
  -> operator classification update
       -> non-qualified: remains outside CRM leads
       -> Qualified Lead: audited promotion transaction
            -> crm_leads + preserved messages
            -> webhook event lead linkage reconciled

CRM lead workspace
  -> complete chronological conversation + normalized requirements + evidence + notes + prior AI runs + cursor
  -> Bedrock primary / Sonnet fallback / Ollama fallback
  -> persisted crm_ai_runs + crm_drafts + provenance
  -> operator review/edit/pre-send grounding
  -> manual WhatsApp action only; no automatic send

Housing_Listings A:AV
  -> CRM reads operational A:AT only
  -> 88-row operational mirror in crm_inventory_snapshot
  -> five-minute reconciliation
  -> crm_inventory_sync_changes records future field-level changes
```

### Test-history checkpoint

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The final repository verification was 71/71 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.



**Source:** `Housing_Listings` tab in the Housing Listings Google Sheet. The legacy Slack flow still writes this sheet; the new CRM sync uses no AWS resources. CRM never writes back to the sheet.

**Implementation:** `src/housing-sheet-adapter.mjs` (read-only OAuth scope), `src/inventory-sync.mjs` (full snapshot, row hashes, transaction, advisory lock, tombstones, field-level change history), `crm-server.mjs` (signed sync endpoint, protected matching API), `src/main.jsx` (live inventory browser view and 60-second refresh). `004_crm_inventory_sync_metadata.sql` and Supabase `crm_inventory_sync_tick()` support the mirror.

**P1–P5 hardening (2026-10-01):** webhook event lead linkage is reconciled during promotion; the webhook recovery job repairs message-backed received/processing states; AU/AV are explicitly excluded from the A:AT CRM projection; `crm_inventory_sync_changes` records future field-level inventory changes; and the repository has a disposable create/edit/delete regression without mutating the production Sheet.

**Current production state (2026-10-01):** The five-minute cron job crm_inventory_sheet_reconcile_5m is active. There are 1,377 recorded sync runs; the latest verified inventory sync is 88 rows / 0 changed / 0 removed.

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
