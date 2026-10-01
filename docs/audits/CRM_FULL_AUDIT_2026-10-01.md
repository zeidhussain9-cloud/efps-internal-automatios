# EFPS CRM Full Production Audit — 2026-10-01

## Scope

Evidence-first audit and hardening of the production CRM UI, Supabase CRM data path, WhAPI webhook path, inventory matching/media path, AI/draft lifecycle, and repository/deployment reconciliation.

Canonical application branch: `crm-ui-dashboard`  
Production service: `easyfind-crm-d01-d05`  
Production WhatsApp source: `+919148338801`  
Supabase project: `qttcutwzehtskfcwxkwj`

## Current live data evidence

Last successful consolidated Supabase queries during this audit recorded:

- `crm_leads`: 186
- `crm_messages`: 6,858
- `crm_webhook_events`: 453
- `crm_contact_classifications`: 307
- `crm_lead_requirements`: 186
- `crm_ai_runs`: 196
- `crm_drafts`: 196
- `crm_ai_cursors`: 186
- `crm_inventory_snapshot`: 88 active Housing rows

Classification evidence:

- Historical extract: exactly 228 classifications.
- Historical qualified: exactly 140; all 140 have `lead_id` and resolve to real CRM leads.
- Global orphan/mismatch checks for classification ↔ lead links: 0.
- Non-qualified classifications have 0 lead mappings.
- Message ↔ lead/classification alignment: 0 orphan/mismatch rows.
- 2,051 messages are unlinked from CRM leads and are associated with non-qualified/unpromoted contact classifications; 0 were found erroneously linked to leads.

Requirements evidence:

- 186/186 leads have requirement rows.
- No orphan/missing requirement rows.
- Requirement JSON mirror checks performed for BHK and tenant type: 0 mismatches.
- No negative budget, invalid enumerated preference, blank array-element, occupancy, or lease-term anomalies were found in the audited rows.
- Requirements are structurally sparse in several fields; this is recorded as data sparsity, not treated as missing information that can be guessed.

AI evidence:

- 196 AI runs, all persisted with status `proposed` at the audited pre-decision checkpoint.
- 196 drafts persisted before this hardening work; 5 were analysis-only rows with empty reply bodies.
- Prior to repair, 744 stored draft evidence references existed; 326 were stale current-message IDs across 65 drafts.
- 325 stale references were resolvable via same-lead historical `source_message_id`; one reference (`2709`) had no defensible current mapping and was removed from the draft pointer only.
- The raw AI run remains retained. The repair added `ai.evidence.reconciled` activity records.

Inventory evidence:

- 88 active Housing rows.
- 71 Available; 17 Rented Out.
- 83 rows have source Cloudinary media URLs; 5 have no source media.
- 829 distinct Cloudinary URLs were enumerated.
- HTTP verification produced 719 completed image responses, 110 timeouts, and 1 completed non-image response (JSON). Therefore the Cloudinary audit is **not fully green**; timed-out and non-image URLs remain to be diagnosed/retried.
- Five direct sample URLs independently returned HTTP 200 image/jpeg before the full enumeration.

Webhook evidence:

- 452 persisted events at the last successful consolidated query.
- 452 processed; 0 received; 0 processing; 0 failed.
- No duplicate `provider_event_id` groups.
- No duplicate `event_fingerprint` groups.
- No orphan event → lead/message links.
- The live Supabase Edge Function `whapi-crm-webhook` was deployed as ACTIVE version 7 with custom header authentication and `verify_jwt=false` because authentication is implemented inside the function.
- The function now performs provider-event idempotency checks for both message payloads and non-message events before persistence.

Legacy AWS path:

Tracked hashes for the legacy AWS webhook/handler files were unchanged between `main` and `crm-ui-dashboard` for the audited files (`handler.py`, `events_handler.py`, `commands.py`, `commands_handler.py`, `interactive_handler.py`, `leads_worker.py`). No change was made to that legacy flow in this audit.

## Application hardening implemented on crm-ui-dashboard

- Server-side lead search added; search no longer filters only the currently loaded page.
- Classification pagination count now reflects active filters and server-side offset/limit.
- Lead workspace AI cursor query now selects by both lead and source, preventing cross-lead cursor leakage.
- Draft creation rejects empty bodies and validates evidence message IDs against the selected lead.
- AI evidence resolution accepts current message IDs and historical source/provider IDs, then stores only current same-lead message IDs.
- AI apply-time requirement evidence rejects unresolved references rather than inventing them.
- Analysis-only AI results no longer create a customer-facing empty draft.
- Lead Property Matches now has the same Cloudinary broken-image/unavailable-image handling as the Inventory screen.
- Activity & History now exposes follow-up scheduling and completion actions with offline/future-date safeguards.
- WhAPI webhook code now treats duplicate provider IDs as already processed rather than reprocessing.

## Validation

Local repository verification on `crm-ui-dashboard`:

- `npm run build`: PASS
- `npm test`: PASS, 76/76
- `npm run test:browser`: PASS, 1/1
- `git diff --check`: PASS
- JavaScript syntax checks for modified server/repository modules: PASS

Render production before the new hardening release:

- Service: `easyfind-crm-d01-d05`
- Auto-deploy: enabled
- Branch: `crm-ui-dashboard`
- Last currently live deployment observed before this release: commit `de45fd09ee63d7450804fb9b39e32007bdc37640`

The new hardening release is not considered production-complete until the subsequent Git push and Render deployment are independently verified.

## 24-item status

| # | Audit item | Status |
|---|---|---|
| 1 | Complete Historical Message Reconciliation | VERIFIED for the 228 classified lead population and current message/link integrity; direct independent replay against the original 5,286-message export was not available in the active checkout |
| 2 | Reconcile Non-Qualified Contact Messages | VERIFIED: non-qualified message records remain outside CRM leads; no erroneous lead links found |
| 3 | Verify All 228 Classification Records | VERIFIED: 228/228 historical records present and populated |
| 4 | Verify All 140 Qualified Lead Mappings | VERIFIED: 140/140 resolve to real leads |
| 5 | Audit Lead Requirements Data | VERIFIED structurally; sparse source fields recorded without guessing |
| 6 | Audit Property Matching Logic End-to-End | CODE-VERIFIED + DB-derived coverage check; production browser path still needs post-release live verification |
| 7 | Audit Cloudinary Property Images | OPEN: 719 valid image responses, 110 timeouts, 1 JSON response across 829 URLs |
| 8 | Audit Complete Lead Workspace Lifecycle | HARDENED + DB-VERIFIED for all 186 leads; follow-up table currently had 0 stored rows |
| 9 | Audit Every CRM Tab and UI State | HARDENED + browser regression verified; production post-release verification pending |
| 10 | Harden Search, Filters, Sorting, Pagination, and Navigation | IMPLEMENTED + tested |
| 11 | Harden Buttons, Actions, Empty States, and Error States | IMPLEMENTED + tested |
| 12 | Verify AI Analysis and Draft Lifecycle | VERIFIED + hardened; analysis-only empty drafts handled safely |
| 13 | Verify AI Run Persistence and Database Reconciliation | VERIFIED: 196 persisted runs; evidence pointers repaired; all current runs were proposed at the checkpoint |
| 14 | Verify Follow-Up and Activity History | IMPLEMENTED + unit tested; no existing follow-up rows to reconcile |
| 15 | Verify Live WhAPI → Supabase Webhook Flow | VERIFIED at database/Edge-function level; new Edge Function version 7 deployed |
| 16 | Verify Webhook Idempotency and Failure Recovery | CODE-VERIFIED + database uniqueness verified; duplicate live replay still requires a post-deploy authenticated replay |
| 17 | Verify AWS Legacy Webhook Remains Untouched | VERIFIED by tracked-file hash comparison |
| 18 | Production Regression Test on Real Data | PARTIAL: live DB evidence verified; post-release authenticated browser regression pending |
| 19 | Update CRM Documentation to Verified State | IN PROGRESS with this audit and current-state pointers |
| 20 | Run Full Build, Unit, Integration, and Browser Tests | VERIFIED: 76/76 and 1/1 |
| 21 | Deploy and Verify Production | IN PROGRESS: code release not yet pushed from this checkout |
| 22 | Reconcile crm-ui-dashboard into main Without Rewriting History | PENDING until final release tree is verified |
| 23 | Verify tree(main) == tree(crm-ui-dashboard) | PENDING until final release tree is verified |
| 24 | Final Production Evidence and Status Audit | PENDING final release, Render, GitHub, and DB post-deploy checks |

## Known open evidence gates

1. Cloudinary has 110 timeouts and 1 non-image response among 829 distinct URLs. No source media is fabricated.
2. Direct comparison against the original 5,286-message SQLite export cannot be rerun from the active local checkout because the source database/export is not present there. The current database reconciliation evidence is therefore limited to stored provenance, 228 historical classifications, message linkage, and repository import guards.
3. A live authenticated duplicate-event replay must be performed after the Edge Function version 7 release.
4. Final tree equality and production deployment evidence must be recorded after the release commit.
