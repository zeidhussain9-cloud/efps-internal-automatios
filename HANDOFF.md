# EFPS CRM — Handoff

## Notion inventory live acceptance follow-up — 2026-11-13

- Supabase `notion-inventory-state` version 6 is ACTIVE with JWT verification enabled. The isolated AWS stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; Lambda `efps-notion-intake` is Active and its existing AWS secret ARNs were reused. No secret values were displayed, copied, rotated, or overwritten.
- GitHub `crm-ui-dashboard` is `61688164b25f7a7a8e6df8248f91987a9c471ef6`; GitHub `main` is `3c66a89e734d02ade5b4865f05c2dcbc99ec655b`. Both point to tree `14717bf1d37afa8d678fc0526026dae357755fdf`. Render was observed live on `61688164`; health and root checks returned HTTP 200.
- In the signed-in production dashboard, the inventory page displayed 104 listings: 87 Available and 17 Rented Out. The source labels identify Housing Listings in Notion and Supabase as its mirror.
- The live Notion edit test changed the test listing's locality; the changed value appeared in Supabase (`source_kind=housing_notion`) and then on the dashboard. A real Notion delete reached Supabase and soft-deleted the row after about one minute. Earlier duplicate replay handler verification returned `already_processed`.
- Restore did **not** complete end to end: after the Notion page was restored from Trash, no new Lambda invocation or Supabase Edge Function POST was observed, and `deleted_at` remained set. The restore worker itself passed a direct invocation check, which does not prove Notion webhook delivery.
- The exact temporary test projection and intake-event records were deleted from Supabase. The test page was permanently deleted from Notion Trash after explicit user approval. The dashboard and Supabase returned to 104 active Notion listings (87 Available, 17 Rented Out); checks found no remaining test record in the two Supabase tables or Notion Trash.
- Google Sheets is not the live dashboard source, and its reconciliation cron is removed. Legacy Sheet-writing compatibility paths remain. The old WhAPI inventory path remains by explicit direction until final cleanup. Notion webhook settings were not changed; the user had confirmed all eight Page events selected.
- GitHub's earlier Inventory Contract check passed 130/130 on the code-bearing release; the latest `61688164` documentation-only commit was not independently shown to rerun that path-filtered check. Other reported release checks are recorded in the CI history below; no new software test was run during this documentation-only update.

> CRM data snapshot: 2026-10-05 (historical; counts were not re-queried in this inventory task). Current inventory intake deployment status: 2026-11-13.

## Initial inventory workflow checkpoint — 2026-11-13 (superseded above)

- Render: `dep-dbrbc8gjo6nc73etsmr0` is LIVE on commit `6b206ddf07515cff2df82140d86ee873e4ea2965`; `/health` and `/` both returned HTTP 200, with no error logs since deployment. GitHub Actions on that commit passed SAM validation, CRM synthetic CI, and CRM UI verification; the Inventory Contract audit failed on reserved-field references, now fixed in local commit `6e16562` and validated locally. Publishing the fix and handoff was rejected by automatic approval review; the remote branch remains at the deployed commit. The dashboard reads the existing Supabase `crm_inventory_snapshot` table with `source_kind='housing_notion'` only; display and interaction behavior are unchanged.
- AWS account `294417174793` in `ap-southeast-2` was confirmed. Isolated stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; Lambda `efps-notion-intake` is Active, Python 3.12, with `LastModified=2026-11-13T07:12:47Z` and CodeSha256 `BWKGDapY+LtrWskHtPWOLr0m8KcS0Ljp83aGkJFYvw4=`.
- The idempotent backfill replay accepted 104 pages and repaired the missing projection. Supabase confirms 104 processed events and 104 active Notion rows: 87 Available and 17 Rented. There are no Sheet-owned snapshot rows and no test-like listings.
- The five-minute `crm_inventory_sheet_reconcile_5m` Supabase cron was unscheduled. Existing Sheets writes remain in legacy Slack/raw-intake compatibility flows only. The old WhAPI `NEW`-delimited inventory listener remains untouched until final cleanup.
- All eight Notion Page events remain selected as already verified by the user. Existing AWS secret ARNs were reused; no values were shown, copied, created, rotated, or overwritten.
- Local checks: production build and 139/139 Node tests, 129 Inventory Contract tests, 88 inventory-module tests, browser regression 1/1, repository audit, projection regression, Python compilation, and SAM lint passed. `git diff --check` is pending final rerun. A fresh container build was unavailable, so the existing Linux SAM dependency artifact was reused.
- At that earlier checkpoint, raw Property Intake with photos still used legacy Sheet/Cloudinary/Maps compatibility steps. No WhatsApp messages were sent. The later live acceptance test and its Trash status are recorded above.

## Production

- Render: srv-darsv560tbcc73cu4ip0
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: crm-ui-dashboard
- Source number: +919148338801
- Supabase: qttcutwzehtskfcwxkwj

## Historical data snapshot (2026-10-05; not reverified in this task)

253 leads; 9,224 messages; 3,025 persisted WhAPI webhook events; 277 AI runs; 214 drafts; 389 classifications; 88 inventory rows (71 Available / 17 Rented Out).
Classification status: 239 promoted, 88 classified, 32 excluded, 3 pending.

## CRM runtime state (last checked 2026-10-05)

Webhook reconciliation is live through the Supabase Edge Function. A WhatsApp chat_id ending in @g.us is a deterministic Group Message signal for pending contacts. Group Message records remain excluded from CRM leads, while promoted leads are preserved. Automatic WhatsApp sending remains disabled; AI output is operator-reviewed and outbound sending is manual.

## Hardening state

Deterministic OOC assignment and D08 documentation are closed. Group Message classification is implemented, schema-gated, audited, backfilled for current pending group contacts, and deployed to the webhook Edge Function. Independent encrypted backup/isolated restore and AWS least-privilege credential rotation remain external infrastructure prerequisites.

## Release procedure

After runtime verification of this release:
1. Confirm Render reports the current crm-ui-dashboard release commit live.
2. Re-run production webhook/inventory/AI integrity queries.
3. Confirm GitHub CI and browser verification pass.
4. Reconcile the verified tree into `main`.
5. Verify both branch trees are identical.

## AI scheduler — intentionally paused

- `crm_ai_scheduler_6h` is **paused** as of 2026-10-04.
- Its implementation and `crm_invoke_ai_scheduler()` function remain in the repository and database.
- The pg_cron trigger has been removed, so no recurring AI scheduler execution is currently scheduled.
- The deterministic classification scheduler remains active independently at `0 * * * *`.
- Reactivation requires an explicit operational decision and a new scheduler activation.

## Deterministic classification engine — current verified

- Deterministic classification is active for source +919148338801; it does not call AI.
- New WhatsApp messages remain attached to the same crm_contact_classifications record while a contact is pending; conversation history accumulates in crm_messages and webhook evidence remains in crm_webhook_events.
- The scheduler runs hourly at 0 * * * * through Supabase Cron job crm_deterministic_scheduler_1h.
- Qualification requires customer-originated intent plus property/requirement evidence. Outbound property messages alone cannot qualify a contact.
- Known operator-confirmed Internal, Personal/Family, Agent/Partner, Vendor/Supplier and Group Message exclusions remain protected.
- New automatic decisions are Qualified Lead or an approved Unqualified classification. Property Listing Sent is legacy/historical only and is never generated by the deterministic engine.
- Insufficient evidence remains Waiting for Classification and is reevaluated when new conversation evidence arrives.
- Deterministically qualified leads persist auto_qualified=true and display AUTO QUALIFIED on the lead card.
- Every deterministic evaluation records rule version, evidence message/event IDs, reason and audit provenance.

## Scheduler Reconcile Audit — current contract

Points **40 Requirement field correctness**, **41 Property-matching inputs**, and **42 Property-matching results** are governed by the single canonical contract in `crm-source-audit-scheduler/AUDIT_CONTRACT.md` and the shared implementation in `src/crm-requirement-match-audit.mjs`. The scheduled runner fails closed unless the combined requirement/matching audit is complete. Do not duplicate or redefine these rules in this document.

Current live population verified 2026-10-05: **253 promoted qualified leads**, **253 normalized requirement profiles**, **0 missing profiles**, and **71 active canonical inventory listings**. Requirement evidence remains a separate provenance layer and is not fabricated by this audit.
