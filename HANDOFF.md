# EFPS CRM — Handoff

## Notion webhook event history — production deployment 2026-11-14

- Commit `ca05141bec073b87c8617c59bf79a40cd16534f9` is pushed to `crm-ui-dashboard`; Render deployment `dep-dbs1f0m417fc73f0cmig` is LIVE.
- Supabase migration `crm_notion_webhook_event_history` is applied to project `qttcutwzehtskfcwxkwj`. It extends the existing `crm_inventory_intake_events` ledger; it does not create a new table and does not write into WhatsApp `crm_webhook_events`.
- Supabase `notion-inventory-state` is ACTIVE v10 with JWT verification enabled. AWS stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; Lambda `efps-notion-intake` is Active, `LastUpdateStatus=Successful`, updated 2026-11-14 08:14:28 UTC. Existing secret ARNs were reused; no secret values were exposed or rotated.
- SAM template validation and non-container build passed. The existing Linux/Python 3.12 dependency package was reused; only the committed `notion_intake.py` was overlaid and byte-compared before deployment. Docker was not used.
- Local validation: Inventory Python 106/106, Notion Edge Function response-contract 6/6, repository Node 145/145, browser 1/1, Deno type-check, Python compilation and `git diff --check` passed. SQL lifecycle, retry, duplicate, history and privilege tests passed locally before applying the same migration to production.
- The Notion `Property Intake — Raw Details & Photos` form view `Submit New Property` was fetched after deployment. It exposes both `Raw Property Data` and `Photos` questions. The data-source description was updated to direct operators to this form and explain processing outcomes.
- Production acceptance is pending the user's first manual submission. Do not create a synthetic production property. After the user confirms submission, reconcile the Notion page, webhook event row, Lambda/CloudWatch worker, Google Sheet row, Cloudinary media, Housing Listings relation, and Supabase inventory snapshot.
- No WhatsApp message or catalogue dispatch was sent. WhAPI webhook function v10 and its `crm_webhook_events` table/records were not changed.
- Production health advisors returned no health findings. Existing security INFO findings for RLS-enabled service-only tables without policies and unrelated unused-index INFO findings predate this migration; they were not broadened or modified here.

## Notion inventory recovery hardening — 2026-11-13

## Notion inventory recovery hardening — 2026-11-13

- Notion Housing Listings is canonical; Supabase `crm_inventory_snapshot` remains the CRM read model.
- Live source-to-projection comparison: 104 active Notion pages / 104 active Supabase rows; 0 missing, 0 orphaned, 0 duplicate active Listing IDs, 0 semantic field mismatches.
- Intake ledger: 104 processed events; 104/104 have a Listing ID and each matches its snapshot row; 0 failed, 0 needs-review, 0 stale-processing.
- Reserved-field repair: `source_group` is blank across all 104 pages. 43 nonblank `inventory_locked` values were cleared; it is blank across all 104.
- Supabase `notion-inventory-state` ACTIVE v9, JWT verification enabled. AWS `efps-notion-property-intake` stack `UPDATE_COMPLETE`; Lambda `efps-notion-intake` Active, Python 3.12, `$LATEST` updated 2026-11-13 15:18:43 UTC.
- A 15-minute EventBridge reconciliation scans active Housing Listings, queues only changed/restored pages, reconciles event-to-listing IDs, and soft-deletes rows missing from the full Notion result. Zero-page results fail closed. Initial mapping repair updated all 104 event Listing IDs. Latest v9 run: 104 checked, 0 accepted, 104 unchanged, 0 further mapping updates, 0 soft-deletes.
- Restore fallback was tested on rented listing `EF-2609-09B5`: a worker soft-delete was reversed by the scheduled reconciliation, returning `deleted_at` to null. This verifies recovery when Notion restore delivery is missed; actual `page.undeleted` webhook delivery was not independently observed. The eight Page event selections remain as user-confirmed; no webhook settings changed.
- Async failures are retained in the 14-day SQS failure queue after 2 retries / 1-hour maximum age. Lambda logs include page ID, event type, webhook event ID, request ID, outcome and duration; CloudWatch retention is 30 days.
- Production dashboard inventory remains 104 (87 Available / 17 Rented Out); `/health` HTTP 200. No lead UI/classification/qualification changes, WhatsApp messages, or catalogue sends.
- Google Sheets reconciliation remains disabled. Legacy Sheet writes and the old WhAPI `NEW` inventory path remain untouched. Raw Property Intake photo/enrichment credentials are a separate unverified path; no secrets were changed.

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


## Active six-task execution — 2026-11-14 (latest verified local state)

- User explicitly prohibited table deletion. No table has been deleted. Existing crm_webhook_events and crm_inventory_intake_events remain intact.
- Notion event history remains in crm_inventory_intake_events; WhatsApp event history remains in crm_webhook_events. Live Notion event rows: 8 (5 processed, 2 ignored/failed outcomes, 1 needs review). This is not proof of complete capture.
- Production Notion-owned inventory projection: 106 active rows. crm_inventory_snapshot.business_status is now a first-class reporting field, backfilled from source_record.status; all 106 currently report Pending. It is distinct from intake_status and listing_state.
- Additive migration 20261114093738_crm_inventory_business_status.sql was applied to Supabase project qttcutwzehtskfcwxkwj. It adds one column and a partial index only.
- Two requested Housing Listings updates were verified in Notion and Supabase. Their business status is Pending; intake status remains Processed; listing availability remains separate.
- Local code now projects, filters and displays business_status. Maps API-unavailable fallback preserves only an original supported short URL and labels it unverified.
- Local validation: Python Inventory + Maps 122/122; Node 146/146; browser 1/1; Vite build PASS; diff check PASS.
- Current UI, Edge Function and Maps fallback changes are uncommitted and not deployed. Render, Supabase Edge Function and AWS Lambda release steps remain.
- Raw Property Intake full-chain acceptance remains pending a real operator submission and runtime credential verification. No synthetic production property was created.
- Notion workspace cleanup has not been performed; no page was archived/deleted without verified evidence.
- Full docs reconciliation, GitHub CI, Render deployment, production smoke tests and main branch reconciliation remain release steps.
