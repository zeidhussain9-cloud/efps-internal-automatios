## Authoritative current CRM UI verification — 2026-10-02

This is the current production checkpoint after the audited CRM UI polish, routing hardening, verification, deployment, and repository reconciliation. Older dated sections remain historical evidence.

- **CRM deployment branch:** `crm-ui-dashboard`
- **Live repository commit:** `d372c1df061b25e77e43c25b77e0718390781461`
- **Application/UI merge commit:** `7911ef574c98610063f0069e738c06b40fd911b2`
- **Render service:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** `dep-davcp8rm8hqs73btm9g0` = **LIVE**
- **Production health:** live fetch of `/health` returned HTTP 200 with `{"ok":true}`
- **Automated verification:** GitHub Actions run #22 passed `npm run build`, `npm test` (84/84), and `npm run test:browser` (1/1) on Node.js 24.21.0 for the verified application candidate. A later documentation-state verification run also passed.
- **Implemented:** stable direct CRM routes and lead deep links; browser-history and lead-tab routing; debounced lead search; restored desktop layout foundations; consolidated UI polish; responsive/mobile behavior; accessibility states; inventory presentation/filtering/sorting surfaces; route/browser regression coverage.
- **Production boundary:** no backend source or API-contract changes were introduced by this UI release. Webhook ingestion/reconciliation, Supabase persistence, classification, AI, inventory data logic, authentication, privacy, and audit backend paths were preserved.
- **Runtime:** Node.js 24.21.0 is explicitly pinned through `.node-version` and package engine constraints; this matches the current Render Node 24 default documented for services created on or after 2026-09-17.
- **Replit defects resolved:** the accidental terminal-output file and Replit-only `.replit` configuration were not carried into the production tree; the deleted desktop CSS foundation was reconstructed from the verified production baseline.
- **Repository state:** `tree(main) == tree(crm-ui-dashboard)` has been verified after the production release reconciliation. No force-push or history rewrite was used on `main`.

## Authoritative current verified state — 2026-10-01 21:55 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **CRM commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **CRM tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **main:** `b2fbf366021852aedd4bf0ec66484ad421fb5662`
- main tree: 908b635b2b7b04bdf3515934de2769393e282c34
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- Render: easyfind-crm-d01-d05 / srv-darsv560tbcc73cu4ip0, deployment dep-dav82h3m8hqs7399j4ug, LIVE.
- **Live Render deployment:** `dep-dav82h3m8hqs7399j4ug` = **LIVE**
- **Live Render commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 186 leads; 6,870 messages; 465 webhook events; 310 classifications; 186 requirements; 196 AI runs; 196 drafts; 186 AI cursors; 88 active inventory rows.
- **Classification status:** 186 promoted; 88 classified; 23 pending; 13 excluded = 310 total.
- **Webhook status:** 465 processed; 0 received; 0 processing; 0 failed.
- **Message reconciliation:** 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 829/829 distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 78/78 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v8.
- **AWS legacy webhook:** no changes in the audited CRM hardening range.
- **24-item CRM audit:** GREEN / VERIFIED.


## Authoritative current closure — 2026-10-01

Evidence snapshot after final verification:
- CRM UI commit: 1c196577fc414be52c8fc889b3886f11e0e9da5d
- CRM UI tree: 908b635b2b7b04bdf3515934de2769393e282c34
- main reconciliation: completed without rewriting main history; current tree is identical to crm-ui-dashboard
- main tree: 908b635b2b7b04bdf3515934de2769393e282c34
- tree(main) == tree(crm-ui-dashboard): TRUE
- Render deployment: dep-dav82h3m8hqs7399j4ug, status LIVE, commit 1c196577fc414be52c8fc889b3886f11e0e9da5d
- Production health: GET /health = HTTP 200, {"ok":true}
- Supabase: 186 leads, 6,870 messages, 465 webhook events, 310 classifications, 186 requirements, 196 AI runs, 196 drafts, 186 cursors, 88 active inventory rows
- Webhook events: 465/465 processed; 0 received; 0 processing; 0 failed
- Message reconciliation: 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0
- Historical classification population: 228/228 source="historical_extract"; 140/140 qualified mappings resolve to promoted leads
- Requirements: 186/186 lead rows have requirement rows; orphan/missing = 0
- AI/drafts: 196/196 draft→AI-run lead mappings valid; stale evidence references = 0; invalid cursor lead links = 0
- Inventory: 88 active rows; 71 Available; 17 Rented Out; invalid media-array rows = 0
- Cloudinary: 829/829 distinct production URLs returned HTTP 200 with image/* content-type using direct HEAD checks from the production-machine network path
- Tests: npm run build PASS; npm test 78/78 PASS; npm run test:browser 1/1 PASS
- Supabase Edge Function whapi-crm-webhook: ACTIVE version 8
- Legacy AWS webhook/handler files: no changes in the CRM hardening commit range
- 24-item audit status: GREEN / VERIFIED

Historical dated checkpoints below remain historical evidence; this block is the current source of truth.


> Historical checkpoint: the earlier audit snapshot is retained below for evidence. The authoritative current state is the 2026-10-01 21:55 IST checkpoint at the top of this file.

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
- Render: easyfind-crm-d01-d05 / srv-darsv560tbcc73cu4ip0, deployment dep-dav82h3m8hqs7399j4ug, LIVE.
- **Production source:** `+919148338801`.
- Supabase CRM: 186 leads; 310 classifications; 23 pending; 186 promoted; 6,870 messages; 465 webhook events, 465 processed, 0 received, 0 processing, 0 failed.
- **AI persistence:** 196 AI runs, 196 proposed; 196 drafts; 186 AI cursors.
- **Inventory:** 88 active Housing rows; 1,377 sync-run records; latest recorded sync = 88 rows / 0 changed / 0 removed; AU/AV remain outside the CRM operational A:AT mirror.
- **Schedulers:** `crm_webhook_reconcile_1m` active every minute; `crm_inventory_sheet_reconcile_5m` active every five minutes.
- **P1–P5:** implemented and production-verified as documented in `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.
- Verification: build PASS; npm test PASS (78/78); browser PASS (1/1).
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
- Production source `+919148338801`: 186 source-linked leads, 309 classifications, 20 pending, 186 promoted, 6,870 messages.
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

Verified current source: +919148338801; current Supabase snapshot has 186 leads, 313 classification rows, 6,881 messages and 476 webhook events. The current dashboard inventory state is 71 Available and 17 Rented Out (88 active snapshot rows).


### Contact Classification

The production UI uses one simple qualification section with two sub-tabs:

- Waiting for classification: pending and non-qualified contacts.
- Total active inventory to CRM: promoted contacts.

The operator workflow is intentionally one action at a time:

Choose classification → Update → database confirms → queue refresh

Non-qualified classifications remain outside CRM. Qualified Lead is the only classification that creates/links a CRM lead and links preserved messages. The browser never treats a selected value as saved until the server confirms the database transaction.

### Dashboard

The dashboard presents daily operational counters and next actions: CRM leads, contacts waiting for classification, **Total available inventory**, and follow-ups due today. The inventory counter uses `crm_inventory_snapshot.listing_state='Available'`, so it excludes Rented Out rows. Open follow-ups are listed below the counters and open directly into the relevant lead workspace.

### Reliability

Classification errors are rendered inline with the server response instead of silently changing the queue. The write endpoint is protected and gated by CRM_CLASSIFICATION_WRITE_ENABLED=true.


## 2026-10-01 — Production security/operator-control closure

D07 is implemented on `crm-ui-dashboard`: protected operator session UX, default sensitive-data masking, explicit/reversible lead archive, CRM-wide audit visibility, explicit audit-recorded CSV export, retention/deletion boundaries, and visible offline/sync states. The browser E2E regression covers the live-record journey.


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

Historical release metadata is superseded by the authoritative current-state block above.

## 2026-10-01 — Final evidence-first 24-item closure

Current live checkpoint: 186 leads, 6,870 messages, 310 classifications, 196 AI runs/drafts, 465 processed webhook events, and 88 active inventory rows.


## 2026-10-02 — Lead Workspace UI and audit-history closure

The Lead Workspace header no longer exposes the redundant “Actual lead” badge or the bulk-import `Priority · Medium` chip. Priority remains stored in `crm_leads.priority` for data compatibility, but that one-time bulk-extraction field is intentionally not rendered in the operator UI.

The Requirements tab is a normalized editable table backed by `crm_lead_requirements`. Enumerated fields use the database-defined allowed values; BHK and preferred-location inputs expose current inventory values as browser datalist suggestions without preventing valid custom requirements. Saves remain protected, transactional and audit-recorded.

Conversation property grouping is evidence-based: explicit property URLs from supported property portals create property-reference sections, and messages explicitly replying to those source-message IDs remain in that property section. Messages without such stored evidence remain in a separate General conversation section and are not guessed into a property.

Audit Activity is now CRM-wide: it reads all `crm_activity` rows rather than only rows with `lead_id IS NULL`, supports date ranges and pagination, and displays the lead ID when an event is lead-scoped. Lead Workspace Activity & History uses the same `crm_activity` table with a `lead_id` filter, so the two views differ by scope rather than by event storage. Date filters support all activity, this month, previous month, last 30 days and custom ranges.

These changes are locally verified on `crm-ui-dashboard` with the repository test suite and browser regression before deployment.

## 2026-10-02 — Audit event categories

Global and lead-scoped audit rows now display a derived category label (Lead, Message, Classification, Requirements, AI, Follow-up, Inventory, Webhook, or System / Operator) alongside the persisted action. The category is presentation-only and does not alter the underlying audit record.


## 2026-10-02 — Lead list and audit filter UI refinement

The Leads Inbox now uses separated production cards with deliberate vertical rhythm instead of visually merging adjacent leads. Each lead card has a consistent outer margin, border, radius and subtle elevation. Lead name and phone are rendered as a single identity row with an explicit gap and baseline alignment; the phone no longer touches the name on narrow screens.

The Lead Workspace no longer renders the one-time bulk-import Priority field. `crm_leads.priority` remains stored for compatibility but is not presented as an operator-facing UI section.

Global Audit Activity and Lead Workspace Activity & History now use the same production date-range control: a single labelled Date range dropdown with All activity, Today, Last 7 days, Last 30 days, This month, Previous month and Custom range. Custom range reveals From/To date fields only when selected. This replaces the previous row of ad-hoc action buttons and gives both audit scopes the same interaction model.
