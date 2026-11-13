# EFPS CRM — Current Verified State

> CRM metrics below were last revalidated 2026-11-12. Inventory release, counts, and Render state were rechecked 2026-11-13.

## Runtime and release

- Production URL: https://easyfind-crm-d01-d05.onrender.com
- Render service: easyfind-crm-d01-d05 / srv-darsv560tbcc73cu4ip0
- Code-bearing release used for signed-in inventory verification: `61688164b25f7a7a8e6df8248f91987a9c471ef6`.
- Subsequent documentation-only updates were published to the deployment branch and auto-deployed. GitHub production health smoke passed on the documentation follow-up. Use the Render service and GitHub branch refs for the current deployment and commit IDs; documentation commits do not change the verified application code.
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

## Inventory synchronization — live acceptance rechecked 2026-11-13

- Canonical editing surface: Notion Housing Listings. The legacy `Housing_Listings` Sheet remains a compatibility path; the dashboard reads active Notion rows from the existing Supabase snapshot.
- Supabase has 104 active `housing_notion` rows (87 Available, 17 Rented). The temporary test snapshot and intake event were removed. The identified test page was permanently deleted from Notion Trash after user approval.
- `notion-inventory-state` is ACTIVE v6 with JWT verification enabled. Lambda `efps-notion-intake` is Active in AWS account `294417174793`. The user confirmed the existing webhook and all eight Page events remain selected; settings were not changed.
- The `crm_inventory_sheet_reconcile_5m` cron is unscheduled. Legacy Sheet writes remain in Slack/raw-intake compatibility flows. The old WhAPI path remains until final cleanup.
- **Verified live:** an edit made in Notion changed the Supabase mirror and was visible in the signed-in production dashboard. A Notion delete event soft-deleted the Supabase row after about one minute. Duplicate handler replay was previously confirmed as `already_processed`.
- **Restore blocker:** a page restored in Notion disappeared from Trash, but no new Lambda invocation or Edge Function request followed; the Supabase row remained soft-deleted. Direct restore-worker behavior passed earlier, but end-to-end webhook delivery is not working/verified. The test data was then explicitly cleaned from Supabase and the Notion page permanently removed.
- Dashboard after cleanup displayed 104 listings: 87 Available and 17 Rented Out. Checks found zero test projection rows and zero test intake events.
- The 104-page backfill and its 104 processed intake events are historical release evidence, not a new backfill run during this check. Existing AWS secret ARNs were reused; secret values were not read or changed.

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

- Earlier code-bearing release CI passed Inventory Contract (130/130), SAM build/validation, CRM build/tests/browser, and Production health smoke. The latest `61688164` commit changes documentation only; Inventory Contract is path-filtered, so a new pass on that docs-only commit is not evidenced here.
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
