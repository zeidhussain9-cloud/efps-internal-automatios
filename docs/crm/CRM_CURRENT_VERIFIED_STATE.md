## Current verified Notion listing-state control (2026-11-14)

The canonical Notion Housing Listings data source now defines listing_state as a SELECT with exactly three options: Available (green), Rented Out (red), and On Hold (yellow). Existing values were preserved: 89 Available and 17 Rented Out at verification; no existing property rows were bulk-edited. This is a Notion schema-only change; no Google Sheets sync, new data flow, Supabase schema change, webhook change, or dashboard code change was introduced. Existing Notion page-property webhook → Lambda → notion-inventory-state → crm_inventory_snapshot → CRM dashboard path remains unchanged.
# EFPS CRM — Current Verified State

## Current release and inventory status — 2026-11-14 (live check)

- Branches main and crm-ui-dashboard are synchronized with identical tracked trees; GitHub advertises exactly these two branch refs.
- Render CRM service srv-darsv560tbcc73cu4ip0 is LIVE; the exact deployment ID and commit are authoritative in Render and are not duplicated here.
- Supabase notion-inventory-state ACTIVE v12; business-status migration registered/applied.
- AWS efps-notion-intake Active; last update successful at 2026-11-14T09:46:50Z; Maps fallback deployed.
- Inventory projection: 106 active Notion-owned rows, 1 soft-deleted tombstone, 0 active blank locality/society rows.
- Two current submissions are Processed and reconciled: VRR Fortuna EF-2611-PAGH; Shobha Royal Pavilion EF-2611-Y5KC. Both have Raw Property Data, Photos, Processed Property relations and matching active Supabase snapshots.
- Notion webhook ledger: 26 observed (5 processed, 18 ignored, 2 needs review, 1 rejected); full delivery coverage is not certified.
- Processing Notes now append each processing outcome on a new line in the same Notion cell. Existing text is retained; status and processing errors continue to be recorded separately in the event ledger.
- Google Sheets status boundary: the connected Housing_Listings tab has a column-E dropdown with Available and Rented Out only; it has zero conditional-format rules. The Sheet11 reference lists no listing_state options. No Google Sheets edit-to-Supabase sync is live; existing property edits sync from Notion Housing Listings page events. The separate Sheet 2 source must be identified before copying its full vocabulary or color rules.
- No database tables deleted. The intentionally paused AI scheduler remains outside this inventory scope.

# EFPS CRM — Current Verified State

> Historical CRM metrics below were last revalidated 2026-11-12. The current inventory release is recorded in the 2026-11-14 block above.

## Runtime and release

- Production URL: https://easyfind-crm-d01-d05.onrender.com
- Render service: easyfind-crm-d01-d05 / srv-darsv560tbcc73cu4ip0
- Signed-in inventory behavior was rechecked against the current live Render deployment; the deployment ID and commit are read from Render at verification time.
- The current release includes the Notion inventory recovery hardening on the implementation branch. Render auto-deploys from `crm-ui-dashboard`; use the live Render service for the current deployment ID and commit. The CRM dashboard UI itself was not modified by this inventory repair.
- Supabase project: qttcutwzehtskfcwxkwj
- Edge Function: whapi-crm-webhook, ACTIVE v10
- Production source: +919148338801

## Production data

- CRM leads: 371; auto_qualified=true: 138; auto_qualified=false: 233.
- Contact classifications: 839 — 371 promoted, 88 classified, 96 pending, 284 excluded.
- CRM messages since 2026-10-05: 18,641.
- WhAPI message events since 2026-10-05: 18,641; all 18,641 linked to crm_messages; 0 active processing errors.
- Original phone-constraint errors: 43; all reconciled and preserved in processing_error_history. Raw payload JSON was not rewritten.
- Phone-null events since 2026-10-05: 6,652; messages are retained without fabricated contact identities.
- Group messages since 2026-10-05: 13,611; 0 linked to a lead timeline. Historical cleanup evidence is in reconciliation_history.
- Deterministic scheduler: 923 completed / 0 failed since 2026-10-05; cumulative run totals 319 candidates, 118 qualified, 8 unqualified, 193 pending.
- AI scheduler remains intentionally paused. No automatic WhatsApp sending is enabled.

## Historical inventory synchronization checkpoint — 2026-11-13 (superseded by the current release block)

- Canonical editor: Notion Housing Listings. The legacy `Housing_Listings` Sheet remains a compatibility path; dashboard reads active Notion rows from the existing Supabase snapshot.
- Full comparison: 104 active Notion pages, 104 active Supabase rows, 0 missing/orphaned/duplicate records, and 0 semantic field mismatches after normalizing Notion rich-text formatting.
- Intake ledger: 104 processed events; 104/104 Listing IDs populated and matching snapshot Listing IDs; 0 failed, needs-review, or stale-processing records.
- Reserved fields: `source_group` blank on all 104 pages; 43 nonblank `inventory_locked` values cleared; it is now blank across all 104.
- `notion-inventory-state` ACTIVE v9 with JWT verification. AWS `efps-notion-property-intake` stack `UPDATE_COMPLETE`; Lambda `efps-notion-intake` Active.
- EventBridge reconciliation runs every 15 minutes, queues only changed/restored pages, repairs event-to-listing mappings, and soft-deletes projections absent from the complete Notion result. Empty results fail closed.
- Initial mapping repair updated all 104 event Listing IDs. Latest v9 reconciliation: 104 checked, 0 queued, 104 unchanged, 0 further mapping updates, 0 soft-deletes.
- Restore fallback test: `EF-2609-09B5` was soft-deleted in Supabase through the worker and automatically reactivated by the scheduled reconciler. Actual Notion `page.undeleted` webhook delivery remains unobserved; the fallback now recovers missed restores within the 15-minute interval.
- Lambda retries Listing ID allocation three times. Async failures retry twice and then enter the 14-day SQS failure queue. Structured event/page/request logs retain 30 days.
- Inventory remains 104 listings: 87 Available and 17 Rented Out. `/health` returned HTTP 200. No CRM UI, lead classification, qualification or WhatsApp behavior changed.
- Source media gap (not a sync failure): 99/104 listings have Cloudinary image URLs. Five Rented Out pages have no image URL in Notion: `EF-2609-608J`, `EF-2609-22H0`, `EF-2609-VDWH`, `EF-2609-7JGF`, `EF-2609-MECJ`. The CRM mirrors the blank source values; no substitute images were invented.
- Sheet reconciliation cron remains removed. Legacy Sheet writes and old WhAPI inventory listener remain untouched. Raw Property Intake photo/enrichment credentials remain a separate unverified compatibility path.

## Slack property batch and review boundary

The Slack intake bot confirmed 17 listing IDs. The active Supabase mirror contains 16 of them:

EF-2611-VN4A, EF-2611-G5ZS, EF-2611-JBVP, EF-2611-ZEFZ, EF-2611-6JYX, EF-2611-97J4, EF-2611-79F1, EF-2611-98PS, EF-2611-Q2GV, EF-2611-WVP3, EF-2611-9ZZJ, EF-2611-XXHD, EF-2611-5NZA, EF-2611-KQ44, EF-2611-3Q39, EF-2611-B42K.

EF-2611-NFHV is not a separate active row. Its Bellandur 2-BHK / ₹40K details are repeated in the later EF-2611-B42K entry, which includes the explicit Semi Gated value and 10 photos. Do not create a second NFHV listing.

Eight original Slack confirmations carried Needs Review warnings. Seven surviving IDs now have internal_property_type=Semi Gated and empty error_notes; the eighth (NFHV) is the duplicate/replaced intake. However, the current mirror does not retain a separate original Needs Review marker or an execution log proving who cleared each warning. WVP3 still has an empty property_subtype, matching the Slack bot's unresolved-subtype warning. Keep WVP3 under review until an operator validates that field. Do not auto-publish or silently clear this warning.

The 16 IDs are confirmed in Supabase. The source Sheet was not reread during this follow-up. The signed-in inventory UI was directly checked and showed 104 properties; this did not revalidate every Slack batch field.

## Webhook and qualification verification

- All 18,641 message events since 2026-10-05 are processed and linked to crm_messages; no active processing errors remain.
- All 43 original errors remain in error history.
- Group messages remain stored but are not attached to personal lead timelines.
- The last two-hour inbound sample was dominated by group/newsletter traffic; it did not provide a fresh one-to-one personal conversation to exercise a new lead promotion.
- The deterministic scheduler continues hourly with 0 recorded failures. AI remains outside the deterministic path.

## CI, UI and verification boundary

- This recovery release passed the full repository build/test/browser suite, 92 inventory-module pytest tests (including 26 Notion intake tests), 4 Edge Function contract tests, SAM build/validation, Python compilation, repository audit, and `git diff --check`. Historical CI checkpoints remain below as dated evidence.
- Earlier local repository audit, projection regression, compileall, SAM lint, and Notion intake tests passed (23/23); CRM browser regression passed 1/1. This docs-only update did not rerun software tests.
- The signed-in production inventory page was exercised: it showed 104 properties and the test listing during the edit check, then returned to 104 listings after cleanup.
- Earlier npm install reported 7 dependency advisories (3 moderate, 4 high); no dependency upgrades were applied.

## Repository and branch state

- Both supported branches, `crm-ui-dashboard` and `main`, were reconciled after the documentation follow-up and have identical tracked trees. Local worktrees were fast-forwarded to their published branch heads.
- Four Dependabot refs remain because their PRs are open: #93, #94, #96 and #97. They are automation PR heads, not additional CRM implementation/deployment branches; do not delete them while those PRs remain open.
- Check GitHub refs for current commit IDs; this document avoids embedding its own commit hash.

## Scheduler policy

| Process | Schedule | State |
|---|---|---|
| crm_webhook_reconcile_1m | Every minute | Active |
| crm_inventory_sheet_reconcile_5m | — | Removed 2026-11-13 |
| crm_deterministic_scheduler_1h | Every hour | Active |
| AI scheduler | Not scheduled | Intentionally paused |

Reactivating the AI scheduler requires a separate explicit operational decision.


## Historical pre-deployment inventory status note — 2026-11-14 (superseded by the current release block)

The live crm_inventory_snapshot table has an additive business_status column, backfilled from source_record.status. At the latest query, all 106 active Notion-owned rows reported Pending. This is distinct from intake_status and listing_state. The CRM UI/API implementation was subsequently deployed; see the current release block at the top of this document. No tables were deleted.
