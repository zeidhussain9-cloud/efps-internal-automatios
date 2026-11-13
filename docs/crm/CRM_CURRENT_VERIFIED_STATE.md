# EFPS CRM — Current Verified State

> CRM production facts below were revalidated 2026-11-12. Inventory ownership and Notion backfill were verified 2026-11-13.

## Runtime and release

- Production URL: https://easyfind-crm-d01-d05.onrender.com
- Render service: easyfind-crm-d01-d05 / srv-darsv560tbcc73cu4ip0
- Live deployment: dep-dbqod1nf3r2c73fe2gc0
- Live commit: d4083c8c33802f33295b090b9b1c4e71453b5090 on crm-ui-dashboard
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

## Inventory synchronization

- Canonical editing surface: Notion Housing Listings. The legacy `Housing_Listings` Sheet remains only for compatibility intake; reserved AU/AV remain outside operational writes. Dashboard reads Notion rows only.
- Current Supabase mirror: 104 active `housing_notion` rows; all 104 corresponding Notion intake records are processed. The isolated Lambda is deployed and the user confirms the existing webhook plus all eight Page events are verified/selected.
- The `crm_inventory_sheet_reconcile_5m` cron was unscheduled on 2026-11-13. No active Sheet reconciliation remains. The current snapshot contains 104 active `housing_notion` rows (87 Available, 17 Rented), no `housing_sheet` rows, and no test-like listings.
- The Notion backfill replay was accepted for 104 pages; all 104 intake events are processed. Dashboard source reads only active Notion rows.
- Confirmed 502 cause: crm_inventory_sync_changes child rows were inserted before the parent crm_inventory_sync_runs row, violating the run_id foreign key. The deployed code inserts the parent first in the same transaction.
- HTTP response history after repair: 12 HTTP 200 responses through 09:55 UTC; the 15 observed HTTP 502 responses were all before 09:10 UTC.

Notion Housing Listings and its Supabase projection were rechecked during this migration. The Sheets reconciliation schedule is disabled. Existing AWS secret ARNs were reused; secret values were not read, printed, copied, created, rotated, or overwritten.

## Slack property batch and review boundary

The Slack intake bot confirmed 17 listing IDs. The active Supabase mirror contains 16 of them:

EF-2611-VN4A, EF-2611-G5ZS, EF-2611-JBVP, EF-2611-ZEFZ, EF-2611-6JYX, EF-2611-97J4, EF-2611-79F1, EF-2611-98PS, EF-2611-Q2GV, EF-2611-WVP3, EF-2611-9ZZJ, EF-2611-XXHD, EF-2611-5NZA, EF-2611-KQ44, EF-2611-3Q39, EF-2611-B42K.

EF-2611-NFHV is not a separate active row. Its Bellandur 2-BHK / ₹40K details are repeated in the later EF-2611-B42K entry, which includes the explicit Semi Gated value and 10 photos. Do not create a second NFHV listing.

Eight original Slack confirmations carried Needs Review warnings. Seven surviving IDs now have internal_property_type=Semi Gated and empty error_notes; the eighth (NFHV) is the duplicate/replaced intake. However, the current mirror does not retain a separate original Needs Review marker or an execution log proving who cleared each warning. WVP3 still has an empty property_subtype, matching the Slack bot's unresolved-subtype warning. Keep WVP3 under review until an operator validates that field. Do not auto-publish or silently clear this warning.

The 16 IDs are confirmed in Supabase. Source Sheet re-read and authenticated inventory UI rendering were not independently repeated in this follow-up.

## Webhook and qualification verification

- All 18,641 message events since 2026-10-05 are processed and linked to crm_messages; no active processing errors remain.
- All 43 original errors remain in error history.
- Group messages remain stored but are not attached to personal lead timelines.
- The last two-hour inbound sample was dominated by group/newsletter traffic; it did not provide a fresh one-to-one personal conversation to exercise a new lead promotion.
- The deterministic scheduler continues hourly with 0 recorded failures. AI remains outside the deterministic path.

## CI, UI and verification boundary

- GitHub Actions CRM UI Verification: PASS; build PASS, 139/139 automated tests PASS, browser regression 1/1 PASS.
- GitHub Actions CRM synthetic CI: PASS; build, unit tests and browser regression passed.
- Production-health smoke job was skipped.
- The authenticated production inventory API/UI was not exercised with an operator session in this follow-up. CI browser regression is not a substitute for an authenticated live inventory read.
- Earlier npm ci reported 7 dependency advisories (3 moderate, 4 high); no dependency upgrades were applied.

## Repository and branch state

- main and crm-ui-dashboard both point to commit d4083c8c33802f33295b090b9b1c4e71453b5090, tree ba5b62470c4bbb97a155451db18dae17229a3133.
- Four Dependabot refs remain because their PRs are open: #93, #94, #96 and #97. They are automation PR heads, not additional CRM implementation/deployment branches; do not delete them while those PRs remain open.
- The owner has deleted all Mac checkouts. No local checkout is retained or required for this verification.

## Scheduler policy

| Process | Schedule | State |
|---|---|---|
| crm_webhook_reconcile_1m | Every minute | Active |
| crm_inventory_sheet_reconcile_5m | — | Removed 2026-11-13 |
| crm_deterministic_scheduler_1h | Every hour | Active |
| AI scheduler | Not scheduled | Intentionally paused |

Reactivating the AI scheduler requires a separate explicit operational decision.
