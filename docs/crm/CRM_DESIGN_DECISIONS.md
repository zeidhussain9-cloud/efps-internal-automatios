# EasyFind CRM — Design Decision Register

**Owner:** Zeid  
**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Working branch:** `crm-ui-dashboard`  
**Figma:** https://www.figma.com/design/PBiMGsVQ0fVpSf39WwNmKb  
**Canva visual reference:** https://canva.link/qmph6ij1o6lue57  
**Updated:** 2026-09-26

## Rules

- Checked items are explicitly approved design decisions; approval does not mean implementation exists.
- No real customer data is used in design mockups.
- Figma is the working design environment; Canva remains the visual reference.
- Live integrations remain disconnected during prototype work.
- Lead data follows the local extraction source-of-truth audit only.
- Inventory UI uses verified Housing Listings field definitions.

## D00 — Baseline — APPROVED

- [x] D00.1 Restrained compact CRM visual direction
- [x] D00.2 Approved Canva reference
- [x] D00.3 Private single-operator CRM
- [x] D00.4 Logical Lead Workspace; no physical Sheet tab per lead
- [x] D00.5 Complete lead workspace capabilities
- [x] D00.6 Human overrides take precedence over AI
- [x] D00.7 AI is explicit/on-demand
- [x] D00.8 Inventory matching is deterministic/source-backed
- [x] D00.9 Preserve raw message history
- [x] D00.10 Draft-first reply safety; no auto-send v1
- [x] D00.11 Design → reconciliation → implementation sequence

## D01 — Navigation & Information Architecture — 6/6 APPROVED

- [x] D01.1 Primary navigation: Dashboard, Leads Inbox, Follow-ups, Inventory, Activity, Settings; Lead Workspace tabs: Overview, Conversation, Requirements, Property Matches, AI & Drafts, Activity & History.
- [x] D01.2 Dashboard is the default landing screen.
- [x] D01.3 Desktop uses focused tabbed Lead Workspace.
- [x] D01.4 Mobile follows Inbox → Lead Workspace → tabbed sections.
- [x] D01.5 Global search, source selector, refresh/freshness and account controls remain in the top bar.
- [x] D01.6 Skeleton, explicit empty, inline error/retry and stale/freshness states; no silent failure.

## D02 — Inbox & Qualification — 9/9 APPROVED

- [x] D02.1 Qualified Leads are primary; Cold/uncertain items go to Review Queue; excluded classifications remain retained outside the primary workflow.
- [x] D02.2 Verified customer name is primary; phone is fallback; EFPS source attribution is preserved.
- [x] D02.3 Lead rows show name, phone, BHK/location, budget max, status, priority, source and activity state.
- [x] D02.4 Default sort latest customer activity first.
- [x] D02.5 Compact filters for source, queue/classification, status, priority, BHK, location, follow-up and needs-analysis state.
- [x] D02.6 Deterministic search across name, phone, BHK, location, tags/notes and conversation text.
- [x] D02.7 Operational counters: Qualified Leads, Review Queue, Needs Attention, Follow-ups Due, New Activity.
- [x] D02.8 Confident duplicates are one logical customer; uncertain identity requires Merge/Keep Separate.
- [x] D02.9 Reclassification is reversible and audited.

## D03 — Lead Workspace — 10/10 APPROVED

- [x] D03.1 Compact persistent lead header.
- [x] D03.2 Chronological stored conversation timeline; Incoming/Outgoing and source attribution.
- [x] D03.3 Visible history boundaries and incomplete-history state when completeness is unproven.
- [x] D03.4 Requirements fields: BHK, locations, budget, furnishing, occupancy, move-in, pets, parking, summary and notes.
- [x] D03.5 Provenance indicators.
- [x] D03.6 Inline manual editing; human value authoritative and audited.
- [x] D03.7 Status/priority controls with activity events.
- [x] D03.8 Follow-up controls.
- [x] D03.9 Activity timeline.
- [x] D03.10 Merge/split with preview, explicit confirmation, audit and reversible history.

## D04 — AI Intelligence & Reply Drafting — 8/8 APPROVED

- [x] D04.1 AI workspace with saved runs/intelligence/new messages/latest draft; explicit invocation only.
- [x] D04.2 First analysis uses the relevant locally available conversation and human-confirmed values with coverage warning.
- [x] D04.3 Versioned saved intelligence, append-only requirement changes/evidence, analyzed message IDs and per-source cursor.
- [x] D04.4 Subsequent analysis uses saved intelligence + new message delta + human edits; explicit full re-analysis.
- [x] D04.5 Proposed requirement changes reviewed with evidence and Accept/Reject/Edit.
- [x] D04.6 Versioned editable drafts; verified inventory references only; copy/open is not send; no auto-send v1.
- [x] D04.7 Every AI attempt, including failure, is preserved.
- [x] D04.8 Visible processing/partial/failed/stale/retry states, correlation ID, idempotent retry and no cursor advance on failure.

## D05 — Inventory Experience — 7/7 APPROVED

**Approved for the UI design on 2026-09-26.** The inventory audit informed the field contract; approval does not mean live inventory integration exists.

- [x] D05.1 Global Inventory screen + contextual Matches panel inside each lead.
- [x] D05.2 Match cards use verified listing ID, locality, BHK, rent, furnishing, availability, match explanation and missing information.
- [x] D05.3 Matching separates mandatory, flexible and Unknown criteria.
- [x] D05.4 Operator can search, pin, exclude or override a suggestion with an auditable reason.
- [x] D05.5 Inventory freshness shows last verified/updated state and unavailable-property treatment.
- [x] D05.6 Share preparation selects verified properties and prepares a verified property summary/draft; preparation/open/copy is not a send.
- [x] D05.7 Per-lead suggested/shared/rejected/visited history is preserved without claiming an unverified send.

## D06 — Live Activity & Webhooks — UNRESOLVED

- [ ] D06.1 New-message indicators and Needs Analysis state.
- [ ] D06.2 Customer number vs EFPS source number distinction for live events.
- [ ] D06.3 Placement of raw webhook event monitor.
- [ ] D06.4 Received/deduplicated/processed/failed/retry/replay states.
- [ ] D06.5 Media edits/deletions/receipts where provider supports them.
- [ ] D06.6 Provider limitation states.

## D07 — Privacy, Safety & Operator Control — UNRESOLVED

- [ ] D07.1 Authentication UX.
- [ ] D07.2 Sensitive-content display/masking.
- [ ] D07.3 Confirmation/reversal/destructive-action patterns.
- [ ] D07.4 Audit visibility.
- [ ] D07.5 Export/retention/deletion UX.
- [ ] D07.6 Failure recovery and offline/sync states.

## D08 — Visual System & Final Handoff — UNRESOLVED

- [ ] D08.1 Typography, spacing and color tokens.
- [ ] D08.2 Reusable CRM components.
- [ ] D08.3 High-fidelity desktop Inbox, Lead Workspace, Inventory and Activity views.
- [ ] D08.4 Corresponding mobile views and fixed primary actions.
- [ ] D08.5 Synthetic edge-case states.
- [ ] D08.6 Accessibility.
- [ ] D08.7 Full operational walkthrough from incoming event → qualification → matching → reply preparation.
- [ ] D08.8 Final visual design freeze.
- [ ] D08.9 Final data-audit handoff.

## Current design gate

**D01–D05 are approved. D06–D08 remain unresolved.**

Approval is a design state only. No live customer/inventory connection or production write is implied.
