# EasyFind Lead CRM — Master Plan

**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Working branch:** `crm-ui-dashboard`  
**Current status:** D01–D05 approved; reconciliation complete; UI implementation not started.

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
Use the verified Housing Listings schema/audit for D05. Live inventory connection comes later.

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

### Phase 1 — Figma completion — NEXT
- [ ] Correct approved D01–D04 screens against the reconciled local-first data model.
- [x] D05 Inventory Experience approved.
- [ ] Create/adjust complete D05 Figma screens.
- [ ] Resolve only the design questions required by the approved flow before implementation.

### Phase 2 — Prototype implementation
- [ ] Build D01–D05 dashboard from synthetic data.
- [ ] Private dashboard shell.
- [ ] Deterministic inbox/search/filter behavior.
- [ ] Lead workspace navigation.
- [ ] Requirements editing simulation.
- [ ] AI workspace simulation/controlled provider boundary.
- [ ] Inventory browse/search/match simulation.
- [ ] Draft preparation simulation.
- [ ] Activity/history simulation.
- [ ] Responsive mobile layout.
- [ ] Automated UI tests.

### Phase 3 — Local-data migration
- [ ] Inspect exact local SQLite file/schema.
- [ ] Reconcile stable source message IDs/duplicates.
- [ ] Migrate source-backed lead/conversation data into the local CRM schema without mutating source evidence.
- [ ] Validate counts and sampling against the lead audit.

### Phase 4 — Live integrations, later
- [ ] Local/verified inventory synchronization.
- [ ] Future WhAPI webhook ingestion.
- [ ] AI production execution.
- [ ] Controlled CRM synchronization.
- [ ] Property-share tracking against real customer data.

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

Prototype implementation can begin only after the approved Figma package matches this branch's `CRM_DATA_MODEL.md`.

Real local-data connection comes after the local SQLite migration/reconciliation gate.
