# Production Live Webhook + Housing Inventory Audit — 2026-10-01

**Scope:** Current production run for the connected CRM WhatsApp source and canonical Housing inventory.

**Repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Branch audited:** `crm-ui-dashboard`  
**Supabase project:** `easyfind-crm` / `qttcutwzehtskfcwxkwj`  
**Primary CRM source:** `+919148338801`  
**Canonical inventory source:** Google Sheet `Housing_Listings`

> This report records evidence from the live production database and the live Housing Sheet. It does not treat historical documentation snapshots as current state.

## 0. P1–P5 hardening closure — 2026-10-01

- **P1 — webhook event lead linkage:** the promotion transaction now reconciles historical webhook rows from their already-linked `crm_messages` relationship. The production migration backfilled the 13 previously eligible rows; current event→message lead mismatch is **0**.
- **P2 — AU/AV contract:** the CRM adapter now explicitly projects only the operational A:AT source range and pads AU/AV as reserved blanks. Regression coverage proves values supplied in AU/AV do not enter the CRM operational projection. No production Sheet values were overwritten.
- **P3 — inventory history:** `crm_inventory_sync_changes` now records create/restore/delete events and field-level old/new values for future changed rows, with source hashes and sync-run IDs.
- **P4 — webhook state recovery:** the production one-minute reconciler now repairs `received`/`processing` events when their durable message already exists, then retries remaining `received` events. The live function invocation was verified after correcting an alias collision; final production checkpoint returned **0 received, 0 processing, 0 failed**.
- **P5 — controlled round-trip regression:** the repository now has a disposable, non-production create/edit/delete inventory round-trip regression over the canonical projection and change-history logic. The production Housing Sheet remains intentionally read-only, so no real listing was mutated.

The five items are implementation/test closure items; they do not authorize changing the Sheet ownership of AU/AV or enabling CRM-side Sheet writes.

## Post-audit live checkpoint — 2026-10-01 12:33 UTC

The current verified checkpoint is **465 persisted webhook events, 465 processed, 0 received, 0 processing, 0 failed**; **6,870 CRM messages**; **310 classifications (23 pending, 186 promoted)**; **186 CRM leads**; and **88 active inventory rows**. The production webhook reconciler and five-minute inventory scheduler are both active. The latest inventory sync record is 88 rows / 0 changed / 0 removed. The verified release is deployed on commit `f492abc0e2a47055eea8b495c9882a7e2033c216` and Render deployment `dep-dav8mrjm8hqs739ajsp0` is live.

## 1. Webhook → Contact → Lead production audit

### Audit window

The active Supabase Edge Function `whapi-crm-webhook` is ACTIVE at version 6. The first persisted live event for `+919148338801` is `2026-09-30 15:51:11.11684 UTC`; the latest event included in this audit is `2026-10-01 11:42:45.50938 UTC`.

### Persisted-event completeness

| Check | Result |
|---|---:|
| `crm_webhook_events` persisted events | **421** |
| Processed | **421** |
| Still `received` | **0** |
| `processing` | **0** |
| Failed | **0** |
| Events with a normalized personal phone | **288** |
| Events linked to a `crm_messages` row | **288** |
| Incoming | **158** |
| Outgoing | **261** |
| Event type | **419 `messages`** |

No persisted live event is stuck, failed, or missing its message row when a personal phone was present.

### Number reconciliation

| Check | Result |
|---|---:|
| Distinct live customer phone numbers | **28** |
| Phones with a classification record | **28 / 28** |
| Live-created classifications | **24** |
| Pre-existing classifications encountered by live traffic | **4** |
| Phones missing a classification | **0** |
| Duplicate classification rows per source+phone | **0** |
| Phones mapped to multiple promoted CRM leads | **0** |
| Live phones with duplicate CRM leads | **0** |

The production flow therefore reconciles each newly observed customer phone to the durable classification registry first. Promotion to the CRM lead layer remains the operator-controlled qualification step.

### Message / lead correctness

Cross-table checks returned:

- event → message row missing: **0**
- message source number mismatch: **0**
- provider message ID mismatch: **0**
- message → classification missing: **0**
- classification phone mismatch: **0**
- classification source mismatch: **0**
- promoted message missing its lead: **0**
- unclassified message attached to a lead: **0**
- promoted classification without a lead: **0**
- duplicate provider event ID groups: **0**
- duplicate event fingerprint groups: **0**
- duplicate source-message-ID groups: **0**

For live messages belonging to promoted classifications, **34** message rows currently point to the correct lead and **0** are missing the promoted lead.

### Historical event-row denormalization — resolved

The audit originally identified **13** pre-promotion webhook rows with a null event-level lead while their preserved message rows already had the promoted lead.

P1 is now implemented in the promotion transaction, and the production hardening migration backfilled the existing 13 eligible rows. The current production invariant is:

- event → message lead mismatch: **0**
- promoted event rows with null lead while their message has a lead: **0**

The event row remains historical evidence; its `lead_id` now records the current resolved lead relationship without changing the preserved message content.

### Group/system event handling

There are **131** outgoing live events with no personal phone. All 131 have a WhatsApp group JID (`@g.us`) and zero have a personal JID. They are therefore correctly excluded from customer-lead reconciliation.

### Webhook verdict

**Verified production state:** persisted webhook ingress, deduplication, customer-number reconciliation, classification linkage, message persistence, and promoted message-to-lead linkage are operationally healthy.

**Webhook data-quality item:** closed by P1. Historical event rows now reconcile their current lead relationship from the durable message linkage.

---

## 2. Housing Sheet → Supabase inventory production audit

### Current live Sheet read

The authorized read-only production Sheet access was used against:

- Spreadsheet: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Physical contract: **48 columns A:AV**

Current live Sheet observations:

| Check | Result |
|---|---:|
| Active rows with `listing_id` | **88** |
| Unique listing IDs | **88** |
| Duplicate listing IDs | **0** |
| Blank/short rows outside active listing set | **6** |
| Column L header | **`google_maps_url`** |
| AU nonblank active rows | **0** |
| AV nonblank active rows | **43** |

### Exact operational-content reconciliation

The CRM inventory adapter reads A:AT and pads reserved AU/AV to blank before hashing. Recomputing the same SHA-256 row hashes from the live Sheet produced this aggregate:

`284f59900fdcfdbcc2c39e8a4cacdb993181b201435ad9f36744c80487330f99`

Supabase `crm_inventory_snapshot` for active `housing_sheet` rows produced the **exact same aggregate SHA-256**:

`284f59900fdcfdbcc2c39e8a4cacdb993181b201435ad9f36744c80487330f99`

Therefore the 88 operational Sheet rows read through the production sync contract are exactly reconciled to the 88 active Supabase inventory rows at the hash level.

Additional current-state checks:

- missing listing IDs in DB: **0**
- extra active DB listings not in Sheet: **0**
- missing source hashes: **0**
- missing last-sync timestamps: **0**
- current source-tab mismatch: **0**
- locality projection mismatches: **0**
- society projection mismatches: **0**
- BHK projection mismatches: **0**
- furnishing projection mismatches: **0**
- listing-state projection mismatches: **0**
- intake-status projection mismatches: **0**
- pet-field projection mismatches: **0**
- duplicate source-hash groups: **0**

### Historical sync/change tracking

The production inventory sync ledger records:

- first recorded Housing sync: `2026-09-26 20:53:54.286275 UTC`
- latest scheduled sync before this audit: `2026-10-01 11:50:02.44293 UTC`
- **1,327** recorded Housing sync snapshots at the final checkpoint
- **9** snapshots with non-zero changes
- initial population: **81** changed rows
- later delta runs: **18** changed-row instances across eight runs
- removals/tombstones recorded: **0**

The live scheduler is:

- job: `crm_inventory_sheet_reconcile_5m`
- schedule: `*/5 * * * *`
- active: **true**
- executions audited: **1,336**
- successful: **1,333**
- failed: **0**
- latest execution: `2026-10-01 11:55:00.077406 UTC`

A manual production reconciliation tick was then run during this audit using the existing sync function. It produced a new sync record at `2026-10-01 11:55:53.572056 UTC` with:

- row_count: **88**
- changed_count: **0**
- removed_count: **0**

No inventory data mutation was introduced by the audit beyond the normal sync-run audit record.

### Reserved-column contract — operationally closed

The live Sheet audit recorded 43 `Yes` values in AV `inventory_locked`. The canonical schema defines AU `source_group` and AV `inventory_locked` as reserved/dummy columns, while the CRM adapter reads only A:AT and pads AU/AV as blank.

P2 is now enforced in the CRM implementation: values supplied in AU/AV cannot enter the operational CRM projection or its operational row hash. No production Sheet values were overwritten because the CRM integration is intentionally read-only.

The 43 source-side AV values therefore remain Sheet-owned metadata outside the CRM mirror; changing or deleting them requires the separate Sheet owner decision and is not part of the CRM reconciliation fix.

### Inventory verdict

**Verified production state:** the live operational inventory rows reconcile exactly to Supabase at the row-hash level; scheduled reconciliation is running every five minutes with zero recorded scheduler failures; the current live tick reports 88/0/0. P2 is closed at the CRM contract boundary.

### Historical granularity limitation

The historical sync ledger remains limited for changes that occurred before P3 was deployed: prior row versions and field-level diffs cannot be reconstructed retrospectively. From this hardening release onward, `crm_inventory_sync_changes` stores field-level old/new values, source hashes, listing IDs, change type, and sync-run IDs, so future edits are reconstructable.

---

## 3. Overall production conclusion

### Verified healthy

**Webhook side**
- Current production webhook rows are processed with **0 received, 0 processing, 0 failed** at the hardening checkpoint.
- Event→message lead mismatch is **0** after the P1 backfill.
- No promoted message is missing its lead.
- The one-minute recovery job is active and now repairs message-backed received/processing states.

**Inventory side**
- 88 current operational Sheet rows reconcile to 88 active Supabase rows at the operational A:AT hash boundary.
- Inventory cron remains active every five minutes.
- crm_inventory_sync_changes provides future field-level change history.
- AU/AV are explicitly excluded from the CRM operational projection.

### Historical limitations that remain factual

1. The 13 pre-promotion event rows are now reconciled to their current lead relationship; their original event-time state remains historical evidence.
2. The 43 AV inventory_locked=Yes source values remain Sheet-owned metadata outside the CRM mirror; the CRM integration does not overwrite them.
3. Field-level inventory edits that occurred before P3 was deployed cannot be reconstructed retrospectively.

These are now documented boundaries rather than open CRM reconciliation defects.
