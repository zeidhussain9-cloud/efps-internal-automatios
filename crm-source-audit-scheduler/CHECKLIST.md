# Scheduler Reconcile Audit — 70-Point Checklist

**Purpose:** Canonical checklist for the EFPS CRM Scheduler Reconcile Audit.

**Status rule:** 🟢 = verified by current production/repository evidence. 🟡 = partially verified; some evidence exists but full reconciliation is not established. 🔴 = not sufficiently verified.

**Current evidence baseline:** 2026-10-05. The production WhAPI API safety hardening is deployed on Render commit 1982c7ea0a158ee0edcb00fad43e021876c13b9d. The shared WhAPI client defaults API access off, hard-blocks non-catalog API operations, and keeps webhook ingestion on as a separate boundary. Therefore the catalog points below are explicitly separated into the last verified external-catalog evidence and what can be verified without making a new WhAPI API request.

| # | Area | Status |
|---:|---|:---:|
| 1 | WhatsApp webhook receives inbound events | 🟢 |
| 2 | Webhook method validation | 🟢 |
| 3 | Webhook authentication | 🟢 |
| 4 | Webhook payload validation | 🟢 |
| 5 | Provider event ID captured | 🟢 |
| 6 | Provider event idempotency | 🟢 |
| 7 | Duplicate webhook detection | 🟢 |
| 8 | Event processing status recorded | 🟢 |
| 9 | Webhook processing failures detected | 🟢 |
| 10 | Event timestamps preserved | 🟢 |
| 11 | Sender/contact identity extraction | 🟢 |
| 12 | Group-chat detection | 🟢 |
| 13 | Group messages excluded correctly | 🟢 |
| 14 | Message body/content extraction | 🟢 |
| 15 | Message direction captured | 🟢 |
| 16 | Message timestamp persisted | 🟢 |
| 17 | Message/provider ID mapping | 🟢 |
| 18 | Event → message reconciliation | 🟢 |
| 19 | Event → contact reconciliation | 🟢 |
| 20 | Contact/message persistence | 🟢 |
| 21 | Missing-message detection | 🔴 |
| 22 | Orphan-message detection | 🟢 |
| 23 | Contact classification record created | 🟢 |
| 24 | Classification status correctness | 🟢 |
| 25 | Classification rule version recorded | 🟢 |
| 26 | Classification reason/signals recorded | 🟢 |
| 27 | Classification evidence message IDs | 🟢 |
| 28 | Customer-originated intent evidence | 🟢 |
| 29 | Property/requirement evidence | 🟢 |
| 30 | Two-gate qualification logic | 🟢 |
| 31 | Group/operator exclusion protection | 🟢 |
| 32 | Deterministic decision persisted | 🟢 |
| 33 | Classification → lead promotion | 🟢 |
| 34 | Lead/source mapping | 🟢 |
| 35 | Qualified-lead completeness | 🟢 |
| 36 | Non-qualified contacts remain outside lead queue | 🟢 |
| 37 | Historical message → classification linkage | 🔴 |
| 38 | Historical lead reconciliation | 🔴 |
| 39 | Lead requirements captured | 🟢 |
| 40 | Requirement field correctness | 🟢 |
| 41 | Property-matching inputs | 🟢 |
| 42 | Property-matching results | 🟢 |
| 43 | Canonical inventory Sheet read | 🟢 |
| 44 | Inventory row count | 🟢 |
| 45 | Inventory create/change/delete reconciliation | 🟢 |
| 46 | Inventory field-level change tracking | 🟢 |
| 47 | Inventory removed/reappeared properties | 🟢 |
| 48 | Inventory sync execution result | 🟢 |
| 49 | Inventory sync error detection | 🟢 |
| 50 | Inventory availability state | 🟢 |
| 51 | Sheet available count → expected catalog count | 🟢* |
| 52 | Actual WhAPI catalog product count | 🟢* |
| 53 | Sheet ↔ WhAPI catalog count reconciliation | 🟢* |
| 54 | Catalog reconciliation completeness | 🟢* |
| 55 | Catalog identity/listing-by-listing match | 🟢* |
| 56 | Catalog field-by-field match | 🔴 |
| 57 | Catalog lifecycle/status reconciliation | 🟢* |
| 58 | Catalog ID ↔ Sheet ID reconciliation | 🟢* |
| 59 | Catalog removed-product reconciliation | 🔴 |
| 60 | Catalog missing-product detection | 🟢* |
| 61 | Products assigned to collections | 🟢* |
| 62 | Products without collections | 🟢* |
| 63 | Collection membership correctness per product | 🔴 |
| 64 | Cloudinary/property-media reconciliation | 🔴 |
| 65 | Deterministic classification run persistence | 🟢 |
| 66 | Activity/audit-history reconciliation | 🟢 |
| 67 | Cross-layer orphan detection | 🟢 |
| 68 | Cross-layer duplicate detection | 🟢 |
| 69 | Incremental “what changed since last audit” | 🔴 |
| 70 | Historical/full-sweep reconciliation and definitive all-green result | 🔴 |

## Current verified interpretation

### 🟢 Verified

Pointers 1–20, 22–36, 39–55, 57–58, 60–62, and 65–68 remain green from verified repository/production evidence. Points 40–42 are also green from production scheduler run 37225973017.

The current production database verification on 2026-10-05 found:
- 253 CRM leads.
- 9,224 CRM messages.
- 3,025 persisted WhAPI webhook events.
- 0 webhook events with failed processing status.
- 389 contact classifications: 253 promoted, 88 classified, 40 excluded, 8 pending.
- 253 normalized lead requirement profiles.
- 88 inventory rows: 71 Available, 17 Rented Out.

The production Render service is live on the WhAPI safety hardening release:
- Deploy: dep-db1b2svf3r2c73brd6m0
- Commit: 1982c7ea0a158ee0edcb00fad43e021876c13b9d
- Branch: crm-ui-dashboard

### Catalog evidence boundary

The starred catalog controls (51–55, 57–58, 60–62) are green based on the last successful external-catalog audit evidence collected before the 2026-10-05 WhAPI API safety lock. They are not evidence that a new live WhAPI catalog read is currently permitted.

The current architecture intentionally prevents accidental WhAPI API requests:
- EFPS_WHAPI_API_ENABLED=false by default.
- EFPS_WHAPI_CATALOG_WRITE_ENABLED=false by default.
- EFPS_WHAPI_WEBHOOK_ENABLED=true by default.
- Non-catalog WhAPI API operations are hard-blocked by the shared client.
- The removed catalog-repair endpoint/workflow is not part of the current production path.

No current documentation may describe a WhAPI catalog read as a live operation unless an independently authorized catalog source is explicitly enabled and verified.

### Last external catalog verification before the safety lock

Scheduler run 37210646893 verified:
- Sheet available products: 71
- WhAPI products: 71
- Listing identity matches: 71
- Missing products: 0
- Catalog-only products: 0
- Duplicate Sheet IDs: 0
- Sheet IDs matched by catalog ID: 71/71
- Products in stock: 71
- Hidden products: 0
- Compared fields: 284
- Field mismatches: 142

Those results are retained as dated evidence. They are not presented as a current live WhAPI read after the safety lock.

### Point 56 — Catalog field-by-field match

**Red.** The last external catalog run reported field mismatches. A later code hardening pass improved semantic media comparison, but no new live WhAPI catalog run was performed after the API safety lock. Therefore point 56 is not greened.

### Point 59 — Catalog removed-product reconciliation

**Red.** No authoritative current external catalog history is available without making a WhAPI API request. Existing CRM inventory state alone does not prove historical external-catalog removal/reappearance reconciliation.

### Point 63 — Collection membership correctness per product

**Red.** A deterministic dry-run against the last available catalog snapshot identified 36 products without collection membership and an exact plan using existing collections:
- 14 → 2BHK
- 18 → 3BHK
- 1 → 1RK & 1BHK
- 3 → 4+ BHK

No new collection names, removals, or unresolved rows were identified in that dry-run. The plan was not applied because the controlled WhAPI write path was subsequently removed and API access was explicitly hardened off. Therefore membership correctness is not claimed.

### Point 64 — Cloudinary/property-media reconciliation

**Red.** Production inventory evidence confirms 71/71 active listings have images, with 696/696 stored image URLs using the Cloudinary URL form and 0 malformed URLs. This establishes the stored source contract, but live URL reachability was not independently verified. Therefore point 64 remains red.

### Points 40–42 — current verified evidence

The canonical contract is crm-source-audit-scheduler/AUDIT_CONTRACT.md and the shared implementation is src/crm-requirement-match-audit.mjs.

Production scheduler run 37225973017 verified:
- 40: 253/253 promoted qualified leads have normalized requirement profiles; 253/253 exactly match the deterministic projection; 0 invalid profiles.
- 41: 253/253 qualified leads produce valid deterministic matcher inputs; 0 invalid inputs.
- 42: 253/253 result sets were valid; 11,482 qualifying lead/listing matches were produced and 30 leads had zero matches. Zero matches are valid evidence.
- No crm_requirement_evidence rows were fabricated by this reconciliation.

### Historical WhatsApp blocker

Historical WhAPI message-list reconciliation remains unavailable because the historical message-list endpoint previously returned HTTP 500. The current webhook path is independent of that historical API and remains operational. This prevents a definitive historical/full-sweep result.

### 🔴 Not sufficiently verified

Pointers 21, 37–38, 56, 59, 63–64, and 69–70 remain red.

There are **no yellow pointers** in the current checklist. A control is either verified under the stated evidence boundary or explicitly left red.

### Final status

**The Scheduler Reconcile Audit is not all-green.** The remaining red controls are evidence gaps, not failures that should be hidden by documentation or assumptions.

The WhAPI safety hardening is intentionally preserved. Do not re-enable WhAPI catalog reads or writes merely to change checklist colors.
