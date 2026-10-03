# EasyFind CRM — Design Decision Register

## Authoritative current verified state — 2026-10-04 00:49 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **Verified deterministic implementation baseline:** `8996dd32d732b0d8fab17f41b42306c230cd1de1`
- **CRM tree:** `c16bafdf7ed4e369d3171a4ee58f80a919630f10`
- **main:** reconciled release branch
- **main tree:** verified equal to crm-ui-dashboard at release close
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** current crm-ui-dashboard release = **LIVE**
- **Live Render:** current crm-ui-dashboard release verified LIVE
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 239 leads; 8,098 messages; 1,831 webhook events; 362 classifications; 186 requirements; 277 AI runs; 214 drafts; 190 AI cursors; 88 active inventory rows.
- **Classification status:** 239 promoted; 88 classified; 32 excluded; 3 pending = 362 total.
- **Webhook status:** 1,831 processed; 0 received; 0 processing; 0 failed.
- **Message reconciliation:** 8,098 total = 6,047 lead-linked + 2,051 classified non-lead; unreconciled = 0.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 829/829 distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 120/120 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v9.
- **AWS legacy webhook:** no changes in the audited CRM hardening range.
- **24-item CRM audit:** GREEN / VERIFIED.

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

## D06 — Live Activity & Webhooks — RESOLVED 2026-09-30

- [x] D06.1 New-message indicators and live workspace refresh are implemented through Supabase Realtime.
- [x] D06.2 Source `+919148338801` and customer phone are distinct persisted fields.
- [x] D06.3 Raw webhook activity is persisted in `crm_webhook_events`.
- [x] D06.4 Webhook states and provider-message idempotency are implemented.
- [x] D06.5 Initial media references and provider message types are persisted; provider-specific edit/delete/receipt events remain unsupported until the provider payload contract requires them.
- [x] D06.6 Unsupported/invalid webhook payloads are retained or rejected with explicit processing state/error.

## D07 — Privacy, Safety & Operator Control — RESOLVED 2026-10-01

- [x] D07.1 Authentication UX — protected operator sign-in with an opaque HttpOnly session cookie, 8-hour inactivity timeout, 12-hour maximum lifetime, explicit logout and failed-sign-in rate limiting.
- [x] D07.2 Sensitive-content display/masking — phone numbers and observed message bodies default to masked presentation; explicit reveal is required for sensitive WhatsApp actions.
- [x] D07.3 Confirmation/reversal/destructive-action patterns — lead archiving requires explicit confirmation, is soft/reversible, and records the previous status plus the restore action.
- [x] D07.4 Audit visibility — global security/operator events are stored in CRM activity and exposed through Activity; lead-specific edits remain in Lead Workspace Activity & History.
- [x] D07.5 Export/retention/deletion UX — CSV export is explicit and audit-recorded; automatic deletion is disabled; permanent deletion is not exposed in v1.
- [x] D07.6 Failure recovery and offline/sync states — offline state is explicit and disables writes/exports; authentication failures return to sign-in; realtime failures remain visible.

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

**D01–D07 are approved/resolved. D08 remains unresolved.**

Approval is a design state only. D06/D07 production controls are tracked separately; D08 remains a design/handoff gate. Current CRM production data and operator classification writes are documented in the current runtime checkpoint.


## Implementation checkpoint — 2026-09-26 (not additional design approval)

**Historical 2026-09-26 provisioning checkpoint:** Supabase Free `easyfind-crm` was provisioned with nine server-only, RLS-enabled tables and a read-only pilot API. That paragraph describes the pre-production gate and is superseded by the later D06/D07 resolution and current production checkpoint. The current production path is source-scoped, authenticated and persisted in Supabase; independent backup/restore remains open and D08 remains unresolved.

## D09 — Simple contact qualification workflow — APPROVED 2026-09-30

- [x] D09.1 One Contact Classification screen; no separate classification filter.
- [x] D09.2 Two sub-tabs: Waiting for classification; Qualified lead pushed to CRM.
- [x] D09.3 One dropdown + explicit Update action per contact.
- [x] D09.4 Non-qualified classifications remain outside CRM.
- [x] D09.5 Qualified Lead is the only promotion path into crm_leads.
- [x] D09.6 Dashboard prioritizes CRM leads, classification queues and follow-ups due today.
- [x] D09.7 Classification failures are visible inline; no silent failure.


## 2026-10-01 — D07 implementation verification

D07 is implemented in the production CRM UI/server path and covered by server/browser tests. The browser E2E regression was traced to the workspace fixture not matching the query-string-bearing production route; the fixture now matches the request and the browser journey performs operator sign-in before reading production surfaces.
