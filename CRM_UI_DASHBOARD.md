# EasyFind CRM UI Dashboard — Single Working Home

## Unreleased production hardening — 2026-10-01

The current crm-ui-dashboard working tree contains the next Inventory hardening release. The four Inventory KPIs are actionable filters rather than static counters: Total properties clears inventory filters, Available filters to available rows, Rented out filters to rented rows, and With photos filters to rows with source media.

Inventory sorting is now a validated request contract through inventory_sort, with latest, oldest, rent_asc, rent_desc, bhk_asc, bhk_desc, and locality_asc. The UI keeps the selected sort visible and the client has a deterministic fallback using the same sort contract. Unknown sort values are rejected with HTTP 400 before database access.

Cloudinary/source media handling now accepts direct URLs, arrays, object media records, JSON-encoded arrays/objects, and comma/newline/pipe-delimited source values. Inventory cards lazy-load images, show explicit unavailable-media states, support retry, and never fabricate photos. The current live Housing mirror has 88 active rows, 83 with source media URLs and 5 without; direct production Cloudinary URL checks returned HTTP 200 image responses for sampled records.

Operator controls were hardened across the shell and lead workspace: interactive buttons now declare their action type, navigation exposes the active page state, offline writes/exports remain disabled, failed lead/requirements/AI/draft/export actions surface a visible error, and failed lead field updates trigger a fresh server read instead of leaving an optimistic local value.

Validation for this working tree: npm run build PASS; npm test PASS (74/74); npm run test:browser PASS (1/1).


## Previous verified repository checkpoint — 2026-10-01

This section is the current checkpoint for maintained documentation. Dated audit sections below remain historical evidence and are not silently rewritten.

- **Canonical UI/deployment branch:** `crm-ui-dashboard`
- **`crm-ui-dashboard` commit:** `da13083f6cb1f3c78ec3f4df661c515d43f556fa`
- **`crm-ui-dashboard` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **`main` reconciliation commit:** `692bdcbbab51752b8eb7d4927921d1cfc4830de7`
- **`main` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**; commit histories differ by design.
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, deployment `dep-dav55km0tbcc73eelat0`, **live**.
- **Production source:** `+919148338801`.
- **Supabase CRM:** 186 leads; 307 classifications; 20 pending; 186 promoted; 6,853 messages; 436 webhook events, 436 processed, 0 received, 0 processing, 0 failed.
- **AI persistence:** 196 AI runs, 196 proposed; 196 drafts; 186 AI cursors.
- **Inventory:** 88 active Housing rows; 1,333 sync-run records; latest recorded sync = 88 rows / 0 changed / 0 removed; AU/AV remain outside the CRM operational A:AT mirror.
- **Schedulers:** `crm_webhook_reconcile_1m` active every minute; `crm_inventory_sheet_reconcile_5m` active every five minutes.
- **P1–P5:** implemented and production-verified as documented in `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.
- **Verification:** `npm run build` PASS; `npm test` PASS (71/71); `npm run test:browser` PASS (1/1).
- **GitHub:** active remote UI branch search returns only `crm-ui-dashboard`; historical UI/inventory branches with deleted remotes are retained only as local historical evidence and are not active deployment branches.

### Current operational flow

```text
WhAPI +919148338801
  -> crm_webhook_events (persist + deduplicate)
  -> webhook processor/reconciler
  -> crm_messages + classification registry
  -> operator classification update
       -> non-qualified: remains outside CRM leads
       -> Qualified Lead: audited promotion transaction
            -> crm_leads + preserved messages
            -> webhook event lead linkage reconciled

CRM lead workspace
  -> complete chronological conversation + normalized requirements + evidence + notes + prior AI runs + cursor
  -> Bedrock primary / Sonnet fallback / Ollama fallback
  -> persisted crm_ai_runs + crm_drafts + provenance
  -> operator review/edit/pre-send grounding
  -> manual WhatsApp action only; no automatic send

Housing_Listings A:AV
  -> CRM reads operational A:AT only
  -> 88-row operational mirror in crm_inventory_snapshot
  -> five-minute reconciliation
  -> crm_inventory_sync_changes records future field-level changes
```

### Test-history checkpoint

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The final repository verification was 71/71 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.



**Canonical working branch: `crm-ui-dashboard`.** Render, GitHub, and the local CRM UI checkout are aligned to this branch for the current production dashboard.

## Current production checkpoint — 2026-10-01

- Render service `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0` is live from the synchronized `crm-ui-dashboard` release.
- Production source `+919148338801`: 186 source-linked leads, 307 classifications, 20 pending, 186 promoted, 6,853 messages.
- Webhook state: 436 persisted events, 436 processed, 0 received, 0 processing, 0 failed; automatic reconciliation remains active.
- Leads Inbox cards now expose only lead status and source number. The Leads Inbox header includes clickable counts for every supported lead status; selecting a status applies the corresponding server-side lead filter.
- AI draft provenance now records input/output/total tokens and an estimated USD cost when standard pricing is known; the draft workspace displays these metrics alongside provider/model provenance.
- Delta/incremental message analysis remains intentionally deferred; AI continues to receive complete chronological lead history.

## Canonical location

**Repository:** https://github.com/zeidhussain9-cloud/efps-internal-automatios  
**Branch:** `crm-ui-dashboard`

`main` is the repository reconciliation branch; Render production remains deployed from `crm-ui-dashboard`. CRM UI implementation work is maintained on `crm-ui-dashboard`, and `main` is reconciled to the same production code/docs checkpoint after each approved release.

## Source of truth

**Leads:** `docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md` + the local SQLite dataset produced by that extraction.

**Inventory:** the live Housing_Listings contract is mirrored into `crm_inventory_snapshot` and consumed by the protected Inventory workspace; reconciliation remains scheduler-driven and the UI presents no fallback inventory.

**Design:** Figma — https://www.figma.com/design/PBiMGsVQ0fVpSf39WwNmKb

**Visual reference:** Canva — https://canva.link/qmph6ij1o6lue57

## Approved state

**D01–D05: APPROVED**

D06 and D07 are resolved in the production CRM path. D08 remains the final unresolved design/handoff stage. D08 is a design/handoff item, not a production-data gate.

## Current rule

Do not use the historical CRM branches as the working location. All future UI dashboard work belongs on `crm-ui-dashboard`.

## Current production workflow — 2026-10-01

Verified current source: `+919148338801`; Supabase has 186 leads, 307 classifications, 20 pending classifications, 186 promoted classifications, 6,853 messages and 436 webhook events, all processed. OOC (`Out of Coverage Area`) is an available Layer-2 lead status. Automatic geographic OOC assignment is not enabled pending a deterministic coverage rule.


### Contact Classification

The production UI uses one simple qualification section with two sub-tabs:

- Not pushed to CRM: pending and non-qualified contacts.
- Qualified leads pushed to CRM: promoted contacts.

The operator workflow is intentionally one action at a time:

Choose classification → Update → database confirms → queue refresh

Non-qualified classifications remain outside CRM. Qualified Lead is the only classification that creates/links a CRM lead and links preserved messages. The browser never treats a selected value as saved until the server confirms the database transaction.

### Dashboard

The dashboard presents only the daily operational counters and next actions: CRM leads, contacts not pushed, qualified contacts pushed, and follow-ups due today. Open follow-ups are listed below the counters and open directly into the relevant lead workspace.

### Reliability

Classification errors are rendered inline with the server response instead of silently changing the queue. The write endpoint is protected and gated by CRM_CLASSIFICATION_WRITE_ENABLED=true.


## 2026-10-01 — Production security/operator-control closure

D07 is implemented on `crm-ui-dashboard`: protected operator session UX, default sensitive-data masking, explicit/reversible lead archive, global audit visibility, explicit audit-recorded CSV export, retention/deletion boundaries, and visible offline/sync states. The browser E2E regression is corrected on the same branch.


## 2026-10-01 — mobile responsiveness and Realtime

The live CRM UI now has an explicit compact/mobile shell through the 1000px breakpoint, including full-width navigation, stacked header/status controls, two-column KPI cards, full-width lead rows and single-column lead workspace content. A browser regression assertion covers a 900px compact viewport so the desktop layout cannot silently regress into the mobile browser experience.

The Supabase browser Realtime client is configured from server-side Render build variables VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY and is initialized after operator sign-in. The channel is notification-only; CRM data remains read from the protected server API. Realtime: live therefore means the browser subscription is active, not that the webhook itself is the source of truth.

## 2026-10-01 — Leads Inbox operational columns

Lead rows/cards now show Contacted date, Last message sent by, and Last message date using the stored CRM conversation timeline. Contacted date is the first Incoming message timestamp; Last message date is the latest message timestamp; Last message sent by is derived from the latest message direction.

The Inbox provides server-side sorting for Last message newest, Customer replied newest, First contacted newest, Last message oldest, and Name A–Z. Sorting occurs before pagination so the operator is not limited to the currently loaded page.

All current source-linked production leads have at least one stored customer message at the 2026-10-01 verification checkpoint; no fixture/default timestamp is used for the new fields.

## 2026-10-01 — Out-of-coverage lead status

Lead Workspace and Lead Inbox support the compact status **OOC** (`Out of Coverage Area`) for leads requesting properties outside the approved service area.

Defined coverage currently includes HSR Layout, Kudlu Gate, Bellandur, Sarjapur Road, Whitefield, Hoodi, Mahadevapura, Marathahalli, ITPL, Varthur, Kasavanahalli, Harlur, Panathur, Koramangala (limited), Yemalur, Bommanahalli (selective), and Old Airport Road (selective).

The status is stored in `crm_leads.lead_type`. The current implementation does not automatically adjudicate free-text locations; that requires a separately verified geographic rule because some listed areas are selective.

## 2026-10-01 — Current live checkpoint
Production: easyfind-crm-d01-d05 (srv-darsv560tbcc73cu4ip0). The current deployment commit is recorded in the final checkpoint below. Bedrock Claude Opus 4.6 (au.anthropic.claude-opus-4-6-v1) is primary; Ollama gpt-oss:20b is fallback. Render startup verified Bedrock configuration presence and Supabase connectivity.

## 2026-10-01 — Current AI generation state

AI provider chain: Bedrock Claude Opus 4.6 (`au.anthropic.claude-opus-4-6-v1`) → Bedrock Claude Sonnet 4.6 (`au.anthropic.claude-sonnet-4-6`) → Ollama `gpt-oss:20b`. Drafts display provider/model/fallback provenance and source-message evidence. Stale drafts are flagged, and the operator must pass a deterministic pre-send check before opening WhatsApp. Sending remains manual; `Mark sent` is an explicit operator audit action. Incremental message analysis remains deferred.

## Final verified checkpoint — 2026-10-01

`crm-ui-dashboard` commit `da13083f6cb1f3c78ec3f4df661c515d43f556fa`, tree `f36a5ccb4bae742e83603b09bee59d01595ecf00`. Render deployment `dep-dav55km0tbcc73eelat0` is live. `main` has been reconciled to the same tree in commit `692bdcbbab51752b8eb7d4927921d1cfc4830de7`. Build passes, `npm test` passes 71/71, and browser regression passes 1/1.
