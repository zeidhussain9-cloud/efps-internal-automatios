# EasyFind Lead CRM — Master Plan

**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Working branch:** `crm-ui-dashboard`  
**Current status (2026-09-26):** D01–D05 approved; initial synthetic React prototype visually approved. Synthetic follow-ups, requirements, activity, settings and inventory search implemented. Render-to-Supabase TLS connectivity is verified with a server-only CA, and GitHub Actions run #81 passed build, all 45 tests and Chromium 1/1. Real customer data remains disabled. See `CRM_STABILIZATION_AUDIT.md` and `CRM_RENDER_CONFIGURATION.md`.

## 1. Product goal

Create a private, operator-first, local-first CRM that turns the manually extracted WhatsApp lead history into one customer workspace and connects that workspace to verified EasyFind inventory.

## 2. Source boundary

### Leads
Use only the local source defined by:
`docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md`

The local SQLite dataset produced by the extraction is the operational lead dataset for this CRM.

Excluded from current lead truth:
- Leads Tracker Google Sheet
- Slack lead reporting/workflow
- DynamoDB lead workflow
- live WhAPI webhook

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
- [ ] Inspect exact local SQLite file/schema.
- [ ] Reconcile stable source message IDs/duplicates.
- [ ] Migrate source-backed lead/conversation data into the local CRM schema without mutating source evidence.
- [ ] Validate counts and sampling against the lead audit.

### Phase 4 — Live integrations, later
- [x] Implement disabled-by-default read-only Sheets adapter and mocked service-account tests; no inventory writes.\n- [ ] Configure later read-only CRM consumption of the existing Slack-maintained Housing Listings Sheet, including edit-audit provenance; service-account JSON belongs in Render only.
- [ ] Future WhAPI webhook ingestion.
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
- No live customer data in the prototype.
- No CRM changes directly on main.

## 6. Implementation gate

Prototype is already deployed and visually approved. Live-data connection remains gated on stabilization, synthetic model evaluation, D06–D08 privacy decisions and exact local SQLite reconciliation.

Real local-data connection comes after the local SQLite migration/reconciliation gate.


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
