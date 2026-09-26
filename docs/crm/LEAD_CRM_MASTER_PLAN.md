# EasyFind Lead CRM — Master Plan

**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Working branch:** `crm-ui-dashboard`  
**Current status (2026-09-26):** D01–D05 approved; initial synthetic React prototype visually approved. Synthetic follow-ups, requirements, activity, settings and inventory search implemented; domain tests and CI added. Deployment/build and browser QA must be independently verified. See `CRM_STABILIZATION_AUDIT.md` and `CRM_RENDER_CONFIGURATION.md`.

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
- [ ] Production-private dashboard shell (optional synthetic-only Basic Auth gate implemented; credentials not configured).
- [x] Deterministic synthetic inbox/source/search/queue/priority sorting logic, with unit tests.
- [x] Initial lead workspace tab navigation.
- [x] Editable synthetic requirements: BHK, locality, budget, furnishing, move-in, pets, parking, occupancy, notes and priority (session-only).
- [x] Provider-unavailable simulation; real Ollama pilot pending.
- [x] Synthetic inventory browse/search/match and explicit no-image fallback; real sheet/photos pending.
- [x] Basic editable draft preparation; versioning pending.
- [x] Session-only activity/history, follow-up scheduling/completion and settings visibility; durable history pending.
- [x] Initial responsive mobile layout; QA pending.
- [x] Chromium browser journey test and CI workflow added for synthetic requirements, persistence, follow-ups, inventory and Settings.\n- [ ] Verify successful CI browser run and deployed build; expand coverage for remaining flows.

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
- [x] Synthetic browser persistence, schema-version/corruption recovery, requirements validation and optional server-side Basic Auth gate implemented.\n- [ ] Verify CI and access behavior; production durable database, backups and full session authentication remain pending. Render preview uses browser-only fictional persistence.
- [x] Add first fictional seed fixtures with known expected extraction outcomes and basic fixture tests (not yet representative of raw-data distributions).
- [ ] Inspect authorized local raw extraction and generate fictional representative fixtures with expected results.
- [x] Implement gated server-side Ollama adapter and mocked unit tests using only fictional fixture IDs; human Accept/Reject UI added.\n- [ ] Verify existing Ollama Render variable names without disclosing or overwriting secrets; enable and run a real synthetic model request after access control.
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
