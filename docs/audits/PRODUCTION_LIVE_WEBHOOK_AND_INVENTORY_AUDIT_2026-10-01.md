# Production Live Webhook + Housing Inventory Audit — 2026-10-01

**Scope:** Current production run for the connected CRM WhatsApp source and canonical Housing inventory.

**Repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Branch audited:** `crm-ui-dashboard`  
**Supabase project:** `easyfind-crm` / `qttcutwzehtskfcwxkwj`  
**Primary CRM source:** `+919148338801`  
**Canonical inventory source:** Google Sheet `Housing_Listings`

> This report records evidence from the live production database and the live Housing Sheet. It does not treat historical documentation snapshots as current state.

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

### Historical event-row denormalization found

There are **13** live webhook rows where:

- `crm_webhook_events.lead_id IS NULL`
- but the corresponding `crm_messages.lead_id` is populated, and
- the classification is now promoted to that lead.

These are pre-promotion events. The contact received the messages before the operator promotion occurred. The promotion transaction backfills the preserved `crm_messages` rows and the lead/classification relationship, but does not backfill the original `crm_webhook_events.lead_id` field.

This is **not a message-to-lead routing failure or data loss**. It is a denormalization inconsistency in the historical webhook-event row. The message/lead graph is correct.

### Group/system event handling

There are **131** outgoing live events with no personal phone. All 131 have a WhatsApp group JID (`@g.us`) and zero have a personal JID. They are therefore correctly excluded from customer-lead reconciliation.

### Webhook verdict

**Verified production state:** persisted webhook ingress, deduplication, customer-number reconciliation, classification linkage, message persistence, and promoted message-to-lead linkage are operationally healthy.

**Remaining webhook data-quality item:** 13 historical webhook rows retain a null event-level `lead_id` after later promotion. This should be treated as a minor denormalization gap if event-row-level lead attribution is required.

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

### Reserved-column exception

The live Sheet currently contains:

- AU `source_group`: **0** nonblank rows
- AV `inventory_locked`: **43** rows containing **`Yes`**

The repository contract currently defines AU/AV as reserved/dummy columns that must remain blank, and the CRM sync deliberately reads A:AT so these reserved values are not copied into the operational CRM mirror.

This means:

- the **operational inventory dataset A:AT is fully reconciled**;
- the live Sheet nevertheless has **43 nonblank AV values that violate the documented reserved/blank contract**;
- those AV values are not represented in the CRM mirror and should not be overwritten without a confirmed ownership decision.

### Inventory verdict

**Verified production state:** the live operational inventory rows reconcile exactly to Supabase at the row-hash level; scheduled reconciliation is running every five minutes with zero recorded scheduler failures; the current live tick reports 88/0/0.

**Remaining inventory data-governance item:** AV `inventory_locked` has 43 live `Yes` values despite the current contract marking AV reserved/blank. This is outside the CRM operational sync boundary and requires a deliberate ownership/cleanup decision.

### Historical granularity limitation

The sync ledger records row counts, row hashes, sync timestamps, and removals, but it does not store prior row versions or field-level diffs. Therefore this audit can prove that every recorded sync converged to the current source state and identify all sync runs with detected row changes, but it cannot reconstruct the exact historical field-by-field edits that occurred between snapshots.

---

## 3. Overall production conclusion

### Verified healthy

**Webhook side**
- 419 persisted live webhook events.
- 419/419 processed; 0 received; 0 failed.
- 288 personal events reconcile to 288 persisted message rows.
- 27 distinct customer phones all have classification records.
- No duplicate lead mappings or provider-message duplicates.
- No promoted message is missing its lead.
- Group traffic is correctly kept out of personal lead reconciliation.

**Inventory side**
- 88 current operational Sheet rows.
- Exact aggregate SHA-256 equality between live Sheet A:AT projection and active Supabase inventory.
- 1,333/1,333 scheduler executions succeeded.
- Latest live sync: 88 rows, 0 changes, 0 removals.
- No active inventory row is missing from the operational mirror.

### Not safe to describe as “100% perfect” without qualification

1. **Webhook event-row denormalization:** 13 historical `crm_webhook_events` rows retain null `lead_id` after their contacts were subsequently promoted. The actual message/lead links are correct.
2. **Housing Sheet contract drift:** 43 active Sheet rows have AV `inventory_locked=Yes`, although the repository contract says AV is reserved/blank and the CRM sync intentionally excludes it.
3. **Historical inventory audit depth:** prior field-level Sheet edits are not reconstructable from the current sync ledger because previous row versions are not retained.

These are data-model/governance limitations, not evidence that current customer messages or operational inventory rows are being lost or misrouted.
