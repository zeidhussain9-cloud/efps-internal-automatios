# EFPS CRM — Handoff

## Notion inventory release follow-up — 2026-11-13

- Supabase `notion-inventory-state` version 6 is ACTIVE with JWT verification enabled. The isolated AWS stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; Lambda `efps-notion-intake` is Active with `LastUpdateStatus=Successful`, last modified `2026-11-13T10:46:00Z`, CodeSha256 `+b4hBplC+2CGZag7HnpSDdmfwDqwuvHqtuSSLoGd/6c=`. Existing secret parameters were reused without printing or changing secret values.
- GitHub `crm-ui-dashboard` source commit `ddb0f6391f99ba9a848fd30c8b03bd5db9c1b53c` and documentation follow-up `cd2060e0817849ec011ec60d399c64b6d11b4cae` have passing `test`, `verify`, `validate-build`, and `Production health smoke` checks. Inventory Contract passed 130/130. Render deployment `dep-dbresd8jo6nc73f1r3k0` is LIVE on `cd2060e`; production `/` and `/health` returned HTTP 200.
- A controlled Notion test created a listing, allocated and wrote `EF-2611-NTX2` back to the Notion page, synced it to Supabase, accepted an edit, suppressed duplicate delivery (`already_processed`), soft-deleted it, and restored it with `deleted_at=null`. Duplicate and lifecycle handler checks used direct Lambda worker invokes for the exact test page; webhook delivery for delete/restore was not independently confirmed.
- The temporary Supabase snapshot and intake rows were deleted; current active inventory is 104 rows (87 Available, 17 Rented), and no test rows remain in either Supabase table. The Notion test page was moved to Trash. The Notion connector cannot permanently empty Trash; its SQL query still counts the trashed page. A signed-in CRM inventory display was not checked because the browser session is at the operator sign-in gate.
- Google Sheets is no longer the dashboard inventory source and its reconciliation cron is removed. Legacy Slack/raw-intake Sheet writes remain; WhAPI stays until final cleanup. Raw photo/enrichment credential validity remains unchecked.
- This follow-up supersedes the earlier deployment and acceptance statements below. Dashboard flow is not called fully ready until an operator signs in to verify the live inventory view and the test page is permanently removed from Notion Trash.

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
