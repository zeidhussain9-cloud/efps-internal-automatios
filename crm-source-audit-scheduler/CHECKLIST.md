# Scheduler Reconcile Audit — 70-Point Checklist

**Purpose:** Canonical checklist for the EFPS CRM Scheduler Reconcile Audit.

**Status rule:** 🟢 = currently verified by production/repository evidence. 🔴 = not yet fully verified by the live scheduler audit. A previously verified 🟢 control is not downgraded without evidence of regression.

**Current evidence baseline:** 2026-10-04. The latest catalog-reconciliation code commit `814fcad604a08a1a0aea9613ab861c559b94544d` is verified **LIVE** on Render. However, the enhanced catalog reconciliation has not yet been proven by a post-deployment successful scheduled audit run; therefore pointers 55–64 remain 🔴.

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
| 18 | Event → message reconciliation | 🔴 |
| 19 | Event → contact reconciliation | 🔴 |
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
| 35 | Qualified-lead completeness | 🔴 |
| 36 | Non-qualified contacts remain outside lead queue | 🟢 |
| 37 | Historical message → classification linkage | 🔴 |
| 38 | Historical lead reconciliation | 🔴 |
| 39 | Lead requirements captured | 🔴 |
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
| 55 | Catalog identity/listing-by-listing match | 🔴 |
| 56 | Catalog field-by-field match | 🔴 |
| 57 | Catalog lifecycle/status reconciliation | 🔴 |
| 58 | Catalog ID ↔ Sheet ID reconciliation | 🔴 |
| 59 | Catalog removed-product reconciliation | 🔴 |
| 60 | Catalog missing-product detection | 🔴 |
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
Pointers **1–17, 20, 22–34, 36, 43–54, 61–62, and 65–68** remain green from the established verified production/repository evidence.

### 🔴 Not yet fully verified
Pointers **18–19, 21, 35, 37–42, 55–60, 63–64, 69–70** remain red because the scheduler does not yet have sufficient live evidence to certify them as fully reconciled.

### Important current blocker
WhAPI historical message-list reconciliation remains unavailable because the WhAPI historical message endpoint was returning HTTP 500. The webhook ingestion path itself remains healthy. This prevents claiming a definitive historical/full-sweep green result.

### Catalog status
The catalog reconciliation implementation is now deployed live at commit `814fcad604a08a1a0aea9613ab861c559b94544d`. The implementation covers identity, field, lifecycle, Sheet-ID, removed-product, missing-product, collection-membership, and media reconciliation. These controls remain 🔴 until a successful **post-deployment** scheduler audit produces and verifies the corresponding live results.

### Final status
**The Scheduler Reconcile Audit is not yet all-green.**

The checklist deliberately does **not** downgrade any previously verified green control because of the new work. Red means the control is not yet certified as fully reconciled by the current live scheduler evidence.
