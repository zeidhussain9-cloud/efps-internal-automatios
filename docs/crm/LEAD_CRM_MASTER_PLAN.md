
## Production checkpoint — 2026-09-30

Historical checkpoint retained below.


## EasyFind Lead CRM — Master Plan

# EasyFind Lead CRM — Master Plan

**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Working branch:** `crm-ui-dashboard`  
**Current status (2026-09-30):** CRM UI production flow is live on `crm-ui-dashboard` / Render `easyfind-crm-d01-d05`. Production source currently in scope is WhatsApp `+919148338801`. Historical CRM records have been reconciled into Supabase, live WhAPI events are persisted to `crm_webhook_events` before downstream reconciliation, and current live messages are being reconciled. Contact classification remains operator-gated; tenant type is a stored requirement rather than a separate lead-header editor. The other two configured source numbers remain visible for later onboarding only.

## 1. Product goal

Create a private, operator-first, local-first CRM that turns the manually extracted WhatsApp lead history into one customer workspace and connects that workspace to verified EasyFind inventory.

## 2. Source boundary

### Leads
Use only the local source defined by:
`docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md`

The local SQLite extraction is the historical source evidence. Supabase is the current production CRM operational store for the reconciled source.

Excluded from the current CRM lead truth:
- Leads Tracker Google Sheet
- Slack lead reporting/workflow
- DynamoDB lead workflow

Live WhatsApp ingestion is now enabled for the current production source: `+919148338801`. WhAPI events are recorded in Supabase `crm_webhook_events` before reconciliation into CRM message/classification/lead records.

### Inventory
The existing Slack automation alone creates and updates the Housing Listings Sheet. The CRM is a read-only consumer of that sheet when the later integration is configured. Preserve the sheet's editor-change audit trail; CRM lead/property interactions have a separate activity history.

## 3. Current approvals

- D00: approved
- D01: approved
- D02: approved
- D03: approved
- D04: approved
- D05: approved
- D06–D08: unresolved

## 4. Delivery sequence

### Phase 0 — Source/repository reconciliation — COMPLETE
- [x] Canonical implementation repository selected.
- [x] Single clean CRM UI branch created from current main.
- [x] Lead source explicitly set to local extraction audit/local SQLite.
- [x] Housing inventory audit retained for D05.
- [x] D01–D05 design decisions reconciled.
- [x] CRM data dictionary established.
- [x] Conflicting/excluded lead systems removed from the forward CRM source path.
- [x] Figma established as working design environment.
- [x] Prototype remains synthetic-data only.

### Phase 1 — Design reconciliation — PARTIAL; approved React preview is working visual baseline
- [ ] Correct approved D01–D04 screens against the reconciled local-first data model.
- [x] D05 Inventory Experience approved.
- [ ] Create/adjust complete D05 Figma screens.
- [ ] Resolve only the design questions required by the approved flow before implementation.

### Phase 2 — Prototype implementation
- [x] Initial synthetic D01–D05 React dashboard deployed (feature-completion pending).
- [x] Synthetic preview Basic Auth credentials detected on Render at 17:41 UTC; production session architecture remains pending.
- [x] Deterministic synthetic inbox/source/search/queue/priority sorting logic, with unit tests.
- [x] Initial lead workspace tab navigation.
- [x] Editable synthetic requirements: BHK, locality, budget, furnishing, move-in, pets, parking, occupancy, notes and priority (session-only).
- [x] Provider-unavailable simulation; real Ollama pilot pending.
- [x] Synthetic inventory browse/search/match and explicit no-image fallback; real sheet/photos pending.
- [x] Basic editable draft preparation; versioning pending.
- [x] Session-only activity/history, follow-up scheduling/completion and settings visibility; durable history pending.
- [x] Initial responsive mobile layout; QA pending.
- [x] Chromium browser journey test and CI workflow added for synthetic requirements, persistence, follow-ups, inventory and Settings.\n- [x] Verify successful CI browser run and deployed build: GitHub Actions `CRM synthetic CI` run #81 passed build, 45/45 unit/integration tests and Chromium browser journey 1/1.\n- [ ] Expand browser coverage for remaining flows.

### Phase 3 — Local-data migration
- [x] Historical source reconciliation completed for the current production source `+919148338801`; 141 source-linked CRM leads are currently stored in Supabase. The earlier planning count was an intermediate checkpoint, not the current production count.
- [x] Add source-backed classification to the production lead workspace.
- [x] Add source-message provenance fields so historical SQLite message IDs are not misrepresented as provider IDs.
- [x] Add read-only preparation and idempotent import scripts for the audited 5,286-message +919148338801 archive.
- [x] Historical conversation/message reconciliation is now active for the current production source; the imported history and subsequent live WhAPI events share the same reconciliation path.
- [x] Reconcile stable source message IDs/duplicates.
- [x] Reconciled source-backed lead/conversation data into Supabase CRM tables without changing source evidence.
- [x] Validated live webhook receipt and downstream processing for the current source; ongoing reconciliation remains idempotent.

### Phase 4 — Live integrations, later
- [x] Implement disabled-by-default read-only Sheets adapter and mocked service-account tests; no inventory writes.\n- [ ] Configure later read-only CRM consumption of the existing Slack-maintained Housing Listings Sheet, including edit-audit provenance; service-account JSON belongs in Render only.
- [x] WhAPI webhook ingestion is enabled for the current production source and writes to `crm_webhook_events` before reconciliation.
- [ ] AI production execution.
- [ ] Controlled CRM synchronization.
- [ ] Property-share tracking against real customer data.

### Phase 2A — Stabilization and synthetic model pilot — ACTIVE
- [x] Deploy initial synthetic React prototype on Render from `crm-ui-dashboard`.
- [x] User visually approved initial D01–D05 interface.
- [x] Record baseline audit and cleanup gates in `CRM_STABILIZATION_AUDIT.md`.
- [x] Implement synthetic Activity, Settings, follow-ups, inventory search/no-image fallback and per-lead pin/exclude state.\n- [ ] Complete production D01–D05: secure auth, durable lead history, real verified inventory media, AI and advanced workflows.
- [x] Extract reusable tested domain logic for queue filtering, matching, validation and follow-ups; add unit tests and CI.\n- [ ] Finish UI component refactor and browser end-to-end tests.
- [ ] Identify genuinely stale CRM files before any deletion.
- [x] Synthetic browser persistence, schema-version/corruption recovery, requirements validation and optional server-side Basic Auth gate implemented.\n- [x] Verify CI and access behavior: protected routes, fail-closed auth, hardened headers and Render health behavior covered by tests.\n- [ ] Replace pilot Basic Auth with reviewed production session authentication; durable database and backup controls remain pending. Render preview uses browser-only fictional persistence.
- [x] Add first fictional seed fixtures with known expected extraction outcomes and basic fixture tests (not yet representative of raw-data distributions).
- [ ] Inspect authorized local raw extraction and generate fictional representative fixtures with expected results.
- [x] Implement gated server-side Ollama adapter and mocked unit tests using only fictional fixture IDs; human Accept/Reject UI added.\n- [x] Verify Ollama endpoint/model presence without disclosing or overwriting secrets; Render startup confirms both variables are present.\n- [ ] Enable and run a real synthetic model request after the pilot access controls are approved.
- [ ] Verify model extraction, incremental updates, matching, draft safety and failure/retry handling.
- [ ] Review D06–D08 and obtain pilot approval before live data.

## 5. Non-negotiable architecture rules

- Local lead data is the CRM lead source of truth.
- Raw source messages remain source-backed and auditable.
- AI is assistive, never the source of truth.
- Human edits take precedence over AI proposals.
- Inventory facts are source-backed and deterministic.
- Draft generation is separate from observed WhatsApp messages.
- No automatic WhatsApp send in v1.
- No silent failures.
- The production CRM UI may display real customer data only through the protected production database path; synthetic fixtures remain separate from production data.
- CRM UI changes are made on `crm-ui-dashboard`; `main` is not the CRM UI deployment branch.

## 6. Implementation gate

The production CRM UI is deployed and using reconciled real data for `+919148338801`. D06–D08 and later source onboarding remain separate future work; they do not gate the current one-number production flow.


## Latest verification checkpoint
- Fixed CI dependency installation: no committed package lockfile exists yet, so CI now uses `npm install` rather than `npm ci` and avoids lockfile-dependent caching.
- Added real HTTP security integration tests for protected content, disabled AI, incomplete access credentials and rejected methods/routes.
- The latest Render deployment and GitHub Actions browser run must be verified before declaring this stage complete. No Render credential values were read or changed.
- Existing Ollama credentials should be inspected by name/presence only at the credential-configuration stage; Sheets service-account JSON must be supplied through Render server-only environment configuration, not the repository.


## Production persistence preparation — latest
- [x] Operator accepted deployed synthetic UI after manually navigating and checking it.
- [x] Added PostgreSQL v1 schema for CRM-owned leads, source numbers, stable-ID-deduplicated conversations, follow-ups, append-only activity, AI proposals, versioned drafts and per-lead property actions. No editable inventory tables.
- [x] Added explicit opt-in migration command, tests and three-source historical deduplication planning; migration is **not** automatically invoked by deployment.
- [x] Verified the Render workspace currently has **no PostgreSQL instance**.
- [x] Supabase `easyfind-crm` provisioned as the sole hosted CRM database; no Render PostgreSQL instance is needed. Render uses the Supabase IPv4 session pooler with server-only CA verification; the startup `SELECT 1` probe connected successfully at 2026-09-26 18:55 UTC. Real data remains disabled. Backup/restore requirements remain open.
- [ ] Implement durable authenticated production CRUD, transaction-safe audited edits and import dry-run; run full synthetic database integration tests.
- [ ] Reconcile 735/23,454 original extraction against curated 308/6,064 subset before importing any real records.
- [x] Verify latest CI unit, HTTP and Chromium results separately from user-approved browser appearance: GitHub Actions `CRM synthetic CI` run #81 passed build, all 45 unit/integration tests and Chromium browser journey 1/1.
- [x] Reconciled the user's reported full service-account JSON with the existing repository credential names; CRM adapter now accepts raw JSON and Base64 forms. Canonical Housing_Listings Sheet ID is verified in `shared/google_sheets/schema.py` and the Render runtime detects a Sheet ID. Read-only Sheets access test remains gated on credential presence and synthetic gate. Ollama endpoint/model are present but not yet exercised.
See `CRM_DATABASE_MIGRATION_GATE.md`.


## Supabase Free — provisioned 2026-09-26
- [x] Created `easyfind-crm` in Efps, Mumbai (`ap-south-1`), project ref `qttcutwzehtskfcwxkwj`; Supabase confirmed $0/month project creation cost.
- [x] Applied server-only CRM core migration: nine RLS-enabled tables; revoked anon/authenticated grants; no browser-facing policies.
- [x] Added three missing foreign-key indexes and committed matching schema migrations.
- [x] Verified schema via SQL: zero customer leads and zero messages; no real data imported.
- [x] Fix the existing Render-to-Supabase server-only connection. Render now recognizes `supabase_session_pooler_ipv4`; `DATABASE_SSL_CA` is present; startup reports `CRM database connectivity: connected` at 2026-09-26 18:55 UTC. No Render PostgreSQL service is needed.
- [ ] Implement and test authenticated durable server CRUD, raw webhook event log, per-source AI cursor, append-only requirement evidence, safe retries and restore-tested independent backups before any real data.
- [ ] Reconcile historical Mac SQLite source with authorized local access, without modifying the source file. Do not use Desktop Commander without explicit permission.
- [x] Verify the repository's canonical Housing Listings Sheet ID and tab: `shared/google_sheets/schema.py` defines the canonical Spreadsheet ID and `Housing_Listings` worksheet. The CRM adapter does not hardcode the ID; it consumes the Render-side Sheet ID. [ ] Verify the server-side Sheets credential and perform a read-only access test.
- [ ] Store media only in Cloudinary; PostgreSQL stores external media references, never media bytes.


## 2026-09-26 — Read-only database integration checkpoint
- [x] Added `src/crm-repository.mjs` with parameterized PostgreSQL health/list/get operations and repository tests.
- [x] Added server-only `/api/db/status`, `/api/db/leads`, `/api/db/leads/:id` routes, gated by `CRM_DB_READ_ENABLED=true`, `DATABASE_URL` and configured Basic Auth; no database write routes.
- [x] Reconciled the database migration gate and canonical data model docs with the provisioned Supabase state.
- [x] Independently verify the new Render deployment and CI, and securely connect Render to Supabase.\n- [ ] Run authenticated application-level DB route checks against the empty schema.
- [ ] Implement full durable CRUD/event/AI-evidence model and restore-tested backups before real customer import. D06–D08 remain unresolved.


## 2026-09-26 — Render credential validation checkpoint
- [x] Added startup-only credential-presence and database-connectivity checks without printing secret values, plus unit tests.
- [x] Sanitized Render startup at 17:41 UTC: DATABASE_URL, DB read opt-in, Basic Auth and Ollama endpoint/model present; database connection failed. Sheets expected-name flags false, not proof that the user's raw JSON credential or hardcoded ID is absent.
- [x] Do not infer correctness from a variable being present alone: startup now checks protected access configuration and the DB handshake. `CRM_REAL_DATA_ENABLED` remains disabled; no live customer data has been imported.


### Runtime audit — 2026-09-26 17:41 UTC (superseded by 18:55 checkpoint)
Supabase `easyfind-crm` (`qttcutwzehtskfcwxkwj`, Mumbai) is ACTIVE_HEALTHY and independently accepts SQL; nine public tables verified. Render startup: `databaseUrlPresent=true`, `databaseReadOptIn=true`, `authConfigured=true`, `authIncomplete=false`, Ollama endpoint/model present, `sheetsCredentialPresent=false`, `sheetsIdPresent=false`, `liveDataEnabled=false`; Render database probe failed with error details withheld. The Google flags check only `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` and `HOUSING_SHEET_ID`; the user reports a full raw JSON credential and hardcoded sheet ID, which require a code/config mapping audit. Supabase is the sole hosted CRM database; do not provision a second Render database. See `CRM_DATABASE_MIGRATION_GATE.md`. Do not import live customer data until connectivity, access and migration gates pass.


### Runtime audit — 2026-09-26 18:55 UTC
- Render configuration flags: DATABASE_URL present, DB read opt-in present, Basic Auth configured/integrity complete, Ollama endpoint/model present, Sheets credential absent, Housing Sheet ID present, live customer data disabled.
- DB endpoint classified as the Supabase IPv4 session pooler on port 5432; DATABASE_SSL_CA present; startup SELECT 1 succeeded.
- GitHub Actions run #81 passed npm install, build, all 45 unit/integration tests, Chromium install and browser journey 1/1.
- Hardening applied: strict Basic Auth parsing, timing-safe credential comparison, security response headers, fail-closed API surface, parameterized SQL, numeric input validation, read-only Sheets scope, A:AT sheet boundary, and secret-safe startup diagnostics.
- Remaining gates are product/data-governance work: final session auth, durable audited CRUD/event model, backup/restore proof, authorized SQLite reconciliation, read-only Sheets credential setup, Ollama synthetic request, D06–D08 approval and live-data migration.


## 2026-09-27 — Inventory snapshot checkpoint (supersedes earlier inventory-pending statements)
- Imported a read-only snapshot of the `Housing_Listings` tab from the locally available `Housing Agent — Listings.xlsx` export into Supabase `crm_inventory_snapshot`: **81 unique listing rows; 65 Available, 16 Rented Out; 76 rows have source Cloudinary URLs**. Only property fields and at most two Cloudinary image URLs per row were imported; no raw listing messages, WhatsApp links or customer contacts were imported.
- Added `003_crm_inventory_snapshot.sql` to source control. The snapshot has RLS enabled, no anon/authenticated table grants and no write path from CRM to the Slack-owned sheet. The export is a point-in-time snapshot, **not a verified live Google Sheets fetch**; live credential/access validation remains pending.
- Added three explicitly fictional `L-TEST-INV-*` leads to Supabase with no phone numbers and append-only seed audit events. The server-only, security-invoker `crm_lead_inventory_matches` view links their requirements to Available inventory by exact BHK and rent ceiling; verified match counts: 20, 23, 10 respectively. These matches are test data, not confirmed customer recommendations. This is database-level matching; the deployed React interface still uses its synthetic browser fixtures until its inventory API/UI is wired.
- Existing historical CI and Render checkpoints remain historical. The expanded browser test on commit `c1d7376` and any later deployment require independent verification. No claim of live Sheets sync, production-ready customer import, encrypted restore proof or final auth is implied.
- Next gates: implement protected inventory and per-lead match API/UI; verify latest CI and Render; set server-only Sheets credential and perform a read-only live fetch with a diff against this export; add scheduled snapshot refresh with source provenance; independent backup and isolated restore; authorized local SQLite reconciliation; synthetic Ollama evaluation; D06–D08 decisions. Leave credential rotation until the final production move.

## 2026-09-27 — Inventory live-sync implementation checkpoint
- `crm-ui-dashboard` only; repository `main` untouched. Supabase migrations `crm_inventory_snapshot_v1`, `crm_inventory_sync_metadata_v1`, and scheduler extensions/function migrations applied. 81 snapshot rows (65 Available) are still the last confirmed database inventory baseline.
- Render deployed commit `a0efd02`: live inventory API is read by the React Inventory and Property Matches views when authenticated and available; synthetic fallback is explicitly labeled. The UI refreshes the inventory API every 60 seconds. Existing lead records are still fictional fixtures.
- Render has the live Google Sheets service account credential and `CRM_HOUSING_SHEET_READ_ENABLED=true`, plus a signed inventory sync endpoint. No new AWS dependency. Full-row source hashes include the Sheet raw text and links for change detection, but raw messages and contact links are deliberately excluded from the CRM `source_record` for privacy.
- Supabase `pg_cron` and `pg_net` were enabled, and `crm_inventory_sync_tick()` was deployed to call the signed Render endpoint. A five-minute schedule was created, but the scheduler Vault HMAC secret could not be provisioned through the available approved tool path. The job was therefore unscheduled rather than left repeatedly failing. **Successful sync runs: zero; live Sheet-to-DB propagation NOT VERIFIED.** Do not claim production-ready synchronization until the same HMAC secret is installed in Supabase Vault and Render, the five-minute job is rescheduled, and add/edit/delete propagation is tested end to end.
- Code build passed; 57 application tests and 8 focused inventory/server tests passed before deploy. Render reports `a0efd02` live. The authenticated live UI browser test and real Sheet mutation round trip are still outstanding.
- Render paid cron was NOT provisioned: the free plan is unsupported. The Supabase scheduler avoids creating a new paid Render service once its secret is configured.

## 2026-09-27 — Inventory UI reconciliation correction
- The live Inventory UI now uses `/api/inventory/overview` (all active database mirror rows, not only available matching rows), with responsive cards, Cloudinary media gallery, detailed property panel, filters and reconciliation totals. Existing lead-matching endpoint continues to restrict to Available properties.
- Latest verified database baseline: 81 current properties = 65 Available + 16 Rented Out; 76/81 have source image URLs. City and state are missing in the current source snapshot on all 81, so locality is shown and city/state is labeled not recorded. A Cloudinary image returned HTTP 200 image/jpeg. UI code deployed on `crm-ui-dashboard` only; see `CRM_INVENTORY_SYNC_RUNBOOK.md` for evidence and remaining scheduler/mutation gates.

## 2026-09-27 — Dedicated CRM AI steering and current gates (supersedes earlier pending AI claims)

- [x] Hosted Ollama `gpt-oss:20b` authenticated and returned the expected five-key fictional proposal in the live Render startup smoke test at 21:25:38 UTC on 2026-09-26.
- [x] Add a dedicated root `steering.md` for this CRM model only. It contains concise EFPS rental-brokerage context, internal-assistant role, strict JSON schema, human authority, untrusted-input handling and inventory/source boundaries. Do not send repository-wide `CORE_STEERING.md` to the model.
- [x] Load and cache steering server-side, enforce a 2-KiB upper bound and keep each model request to one compact system message and one fictional enquiry. No local model installation, browser-side API key, repeated retrieval or automatic calls on page navigation.
- [x] Add steering-specific tests; verify complete application, build, browser and CI results separately.
- [x] Independently verified the steering-bearing Render `49b4f30` hosted request: success at 2026-09-26 21:36:16 UTC, five expected keys. Optional startup smoke disabled in Render; config deployment `dep-das3lspa4omc738mqre0` reached live at 2026-09-26 21:37:57 UTC with Supabase connected and no model startup call.
- [ ] Finish representative synthetic extraction evaluation, durable audited CRUD, independently restore-tested encrypted backups, 735/23,454/966 source reconciliation and D06–D08 approvals before any real customer import.
- [ ] Production-grade operator session auth, retention policy and final credential rotation remain gated. `CRM_REAL_DATA_ENABLED` remains a separate gate; production contact classification writes use `CRM_CLASSIFICATION_WRITE_ENABLED`.

## 2026-09-27 — Canonical main-branch promotion

Historical branch-reconciliation note superseded on 2026-09-30: `crm-ui-dashboard` remains the Render deployment branch; `main` and `crm-ui-dashboard` are reconciled to the same repository state. The active CRM checkout is `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/crm-ui-dashboard`; the separate `main` worktree is `/Users/zeidzakir/Projects/efps-internal-automatios`. Render remains on `crm-ui-dashboard`; repository reconciliation to `main` is separate. This is a repository reconciliation, not completion of production migration gates.

## 2026-09-30 — Live lead-only webhook completion checkpoint

- [x] Replaced the proposed listener model with a single lead path for the CRM live flow. No inventory listener, lead listener, CRM listener, staged-contact intake or qualification gate exists in the CRM path.
- [x] Deployed Supabase Edge Function `whapi-crm-webhook` as the live WhAPI ingress for source `+919148338801`; Render is not the webhook receiver and AWS is not a CRM runtime dependency.
- [x] Added durable `crm_webhook_events` activity/audit storage with provider-message idempotency and received/processing/processed/failed states.
- [x] New source-phone activity is held in `crm_contact_classifications` with `pending` status and preserved `crm_messages`; it does not create a `crm_leads` row until an operator selects Qualified Lead. Existing promoted contacts continue to append to their lead.
- [x] Removed CRM intake tables and Render intake routes. There is no separate new-contact staging model.
- [x] Historical SQLite evidence remains 5,286 messages; current Supabase production state is 141 source-linked leads and 6,561 messages for `+919148338801`.
- [x] Workspace message ordering is chronological by provider `message_at`, with source/provider identity preserved separately.
- [x] Added sanitized Supabase Realtime broadcast after message insertion so the UI refreshes live without polling WhAPI or polling the CRM workspace.
- [x] Removed the Render-side WhatsApp ingestion route; the old CRM WhatsApp environment gate remains disabled.
- [x] Verified the Edge Function with correct authentication (HTTP 200) and incorrect authentication (HTTP 401). Transactional lead/message processing was exercised and rolled back; persisted counts remained 228/5,286.
- [ ] Final provider cutover: update the connected WhAPI channel's `messages` webhook URL/header to the deployed Supabase function. The available local provider credential did not resolve to an active usable WhAPI channel during this checkpoint, so no provider setting was guessed or changed.

## 2026-09-30 — UI/data-model reconciliation checkpoint

- [x] Contact Classification is now an actual pre-lead registry: the user sees phone/source/status and can classify the contact; Qualified Lead is the only classification that promotes into `crm_leads`.
- [x] Verified source selector contains all three audited EFPS WhatsApp source numbers: `+919148338801`, `+917975102130`, `+919902024973`. The currently connected live WhAPI ingress remains `+919148338801`; the other two are selectable data scopes and are not claimed as live webhook channels.
- [x] Lead Workspace now exposes an operator-editable **Lead Status** dropdown backed by `crm_leads.lead_type`; the label is no longer presented as lead qualification.
- [x] Added operator-editable **Tenant Type** persisted in `crm_leads.tenant_type` with Family, Bachelors, Couples, Students, Working Professionals, Corporate, Other and Not specified values.
- [x] Lead status and tenant type updates use the protected CRM API and write an append-only activity event in the same transaction.
- [x] Leads Inbox supports server-side filters for Lead Status and Lead Source Number.
- [x] Dashboard now reports CRM lead count, waiting-to-be-classified count, live-WhAPI-qualified-lead count and webhook error count for the selected source. It no longer presents a hardcoded historical message count as the live lead metric.
- [x] Realtime diagnostics now surface the actual channel error alongside the connection state instead of only showing `Realtime: error`.
- [x] Applied production migration `20260930145131` (`crm_lead_status_tenant_type_and_webhook_gate_reconciliation`) and verified `crm_leads.tenant_type` plus the reconciled no-auto-lead webhook processor in Supabase.
- [x] Current production evidence after this migration: 141 source-linked `crm_leads`, 287 source classifications for `+919148338801`, 58 pending classifications, 6,561 current `crm_messages`, and 28 persisted webhook events (13 processed, 15 received).
- [x] Local production build, all 62 unit/integration tests, and the Playwright browser journey pass. The browser journey now covers the live-record surface, Lead Status/Tenant Type controls and persisted-update API path.

## 2026-09-30 — CRM daily workflow resolved

- [x] Replaced the separate classification filter with one two-tab Contact Classification queue.
- [x] Not pushed to CRM contains pending and non-qualified contacts.
- [x] Qualified leads pushed to CRM contains promoted contacts.
- [x] Added explicit dropdown → Update workflow with visible saving/error state.
- [x] Qualified Lead promotion is transactional and links preserved messages before queue movement.
- [x] Added Dashboard daily counters and next open follow-ups.
- [x] Classification writes are protected by CRM_CLASSIFICATION_WRITE_ENABLED=true.
