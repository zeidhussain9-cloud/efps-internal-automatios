# Scheduler Reconcile Audit — 70-Point Checklist

**Purpose:** Canonical checklist for the EFPS CRM Scheduler Reconcile Audit.

**Status rule:** 🟢 = verified by current production/repository evidence. 🟡 = partially verified; some evidence exists but full reconciliation is not established. 🔴 = not sufficiently verified. A previously verified 🟢 control is not downgraded without evidence of regression.

**Current evidence baseline:** 2026-10-04. Post-deployment scheduler run **37210646893** completed successfully against the deployed catalog-reconciliation code. It verified 71 Sheet-available products against 71 WhAPI products, with 71 listing identities matched, 0 missing, 0 catalog-only products, 0 duplicate Sheet IDs, 71/71 Sheet IDs matched by Meta/WhAPI catalog ID, 71 in-stock products, and 0 hidden products. Field reconciliation found **142 mismatches across 284 compared fields**, so field-level catalog reconciliation is not green. Removed-product reconciliation is not independently established because the current implementation reports a placeholder 0/0 rather than a historical removed-product sweep. Collection-expectation derivation returned 0 derivable BHK rows in this run, so per-product expected collection correctness is not established.

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
| 18 | Event → message reconciliation | 🟡 |
| 19 | Event → contact reconciliation | 🟡 |
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
| 35 | Qualified-lead completeness | 🟡 |
| 36 | Non-qualified contacts remain outside lead queue | 🟢 |
| 37 | Historical message → classification linkage | 🔴 |
| 38 | Historical lead reconciliation | 🔴 |
| 39 | Lead requirements captured | 🟡 |
| 40 | Requirement field correctness | 🔴 |
| 41 | Property-matching inputs | 🔴 |
| 42 | Property-matching results | 🔴 |
| 43 | Canonical inventory Sheet read | 🟢 |
| 44 | Inventory row count | 🟢 |
| 45 | Inventory create/change/delete reconciliation | 🟢 |
| 46 | Inventory field-level change tracking | 🟢 |
| 47 | Inventory removed/reappeared properties | 🟢 |
| 48 | Inventory sync execution result | 🟢 |
| 49 | Inventory sync error detection | 🟢 |
| 50 | Inventory availability state | 🟢 |
| 51 | Sheet available count → expected catalog count | 🟢 |
| 52 | Actual WhAPI catalog product count | 🟢 |
| 53 | Sheet ↔ WhAPI catalog count reconciliation | 🟢 |
| 54 | Catalog reconciliation completeness | 🟢 |
| 55 | Catalog identity/listing-by-listing match | 🟢 |
| 56 | Catalog field-by-field match | 🔴 |
| 57 | Catalog lifecycle/status reconciliation | 🟢 |
| 58 | Catalog ID ↔ Sheet ID reconciliation | 🟢 |
| 59 | Catalog removed-product reconciliation | 🔴 |
| 60 | Catalog missing-product detection | 🟢 |
| 61 | Products assigned to collections | 🟢 |
| 62 | Products without collections | 🟢 |
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
Pointers **1–17, 20, 22–34, 36, 43–54, 55, 57–58, 60–62, and 65–68** are green from current production/repository evidence.

### 🟡 Partially verified
Pointers **18, 19, 35, and 39** have meaningful evidence but are not fully reconciled.

- **35:** 248 qualified leads exist; 186 have structured requirement rows and 62 do not.
- **39:** Requirement storage is operational for 186 qualified leads, but 62 qualified leads have no structured requirement row.
- Requirement evidence is currently absent, so this does not establish field-level correctness.

### 🔴 Not sufficiently verified
Pointers **21, 37–38, 40–42, 56, 59, 63–64, and 69–70** remain red.

### Historical WhatsApp blocker
WhAPI historical message-list reconciliation remains unavailable because the historical message endpoint has returned HTTP 500. The webhook ingestion path itself remains healthy. This prevents a definitive historical/full-sweep result.

### Catalog evidence from scheduler run 37210646893
- Sheet available: **71**
- WhAPI products: **71**
- Listing identity matches: **71**
- Missing products: **0**
- Catalog-only products: **0**
- Duplicate Sheet IDs: **0**
- Sheet IDs matched by catalog ID: **71/71**
- Products in stock: **71**
- Hidden products: **0**
- Compared fields: **284**
- Field mismatches: **142**
- Removed-product historical reconciliation: **not established**
- Collection expectation derivable from BHK: **0** in this run
- Products with collections: **35**
- Products without collections: **36**

The 142 field mismatches are actual evidence, not a software failure. The scheduler completed successfully and surfaced differences that must be reconciled before point 56 can be green.

### Final status
**The Scheduler Reconcile Audit is not all-green.**
