
## CRM production checkpoint — 2026-09-30

Historical checkpoint retained below.


## Current state

## Current state

The active workstream is the **production CRM UI on `crm-ui-dashboard`**. The current production source is WhatsApp `+919148338801`; historical and live data reconcile through Supabase. The other two configured source numbers remain visible in the UI for later onboarding.

The authorized implementation target is **Inventory Management Phase 1**. The workflow has three top-level stages: Stage 1 Initial/Webhook, Stage 2 Deterministic Extraction/Property Processing, and Stage 3 downstream boundary reserved for later consumers.

## Stage-2 implementation truth

- `extract.py` discovers deterministic source facts from completed `raw_message_text`.
- `source_segments.py` is the canonical source-message boundary parser for concatenated WhatsApp inventory messages.
- `field_resolution.py` is the canonical candidate-resolution layer for BHK, maintenance, and internal property type.
- `pipeline.py` is the authoritative deterministic processing boundary and passes resolved internal property type explicitly into normalization.
- `normalize.py` consumes canonical resolved property type and must not independently reclassify it.
- BHK preserves decimals and later explicit corrections.
- Maintenance requires maintenance-specific context, normalizes K/lakh units, independently evaluates inclusion, and preserves source qualifiers such as `+ Water`.
- Internal property type has exactly three business values: Gated Community, Semi Gated, and Standalone. Explicit source classification wins; casing and ordinary spacing/hyphenation variants are accepted; missing or invalid classification remains unresolved and never implies Standalone.
- Numeric balcony extraction covers explicit singular/plural source forms, including bare `Balcony` as one balcony.
- Explicit no-pet source wording is authoritative during final normalization.
- `📍 Landmark:` followed only by a Maps URL remains a blank landmark; the URL belongs to `google_maps_url`, and landmark never inherits locality.
- Existing Sheet Stage-2 values are never deterministic extraction input.
- `Needs Review` is governed by `docs/NEEDS_REVIEW_CONTRACT.md`; non-blocking field gaps do not become property-processing blockers by themselves, but they must still remain deterministic and contract-valid.

## Canonical dependency contract

```text
internal_property_type -> society_amenities
internal_property_type -> covered_parking (blank-only default)
furnish_type -> flat_furnishings (blank-only default)
preferred_tenant_type -> bachelor_preference
maintenance -> maintenance_included
built_up_area -> carpet_area (blank-only fallback)
monthly_rent -> security_deposit (month-based source form)
```

For tenant eligibility:

- `preferred_tenant_type` has exactly two live Sheet values: `Family` and `Open For All`.
- `Family` -> `bachelor_preference` is blank.
- `Open For All` -> `bachelor_preference` defaults exactly to the Sheet dropdown value `Open for both`.
- Explicit valid source evidence for `Female Only ` or `Male Only` overrides the default.
- `Female Only ` includes the intentional trailing space present in the live Sheet dropdown and that exact value is the canonical contract.

## Verification / operating boundary

The canonical normal path is:

```bash
PYTHONPATH=.:modules/efps-inventory-mgmnt python tools/run_phase1_rows.py --start-row <n> --end-row <m>
```

The normal runner skips rows already marked `Processed`; already-processed rows use the controlled dependency-repair tool `tools/repair_phase1_dependencies.py`. Live production processing must start only from an exact local checkout of the accepted `main` commit and after the regression/audit suite passes locally.

No production credentials or secrets are part of the repository hardening.

## Live operational boundary

- Lead Management behavior, persistence, audit, cards, dashboard, stream worker, and Slack endpoints present on `main`.
- The canonical WhAPI webhook boundary, with direct inbound traffic routed to Lead and the two configured inventory listeners routed only to Inventory Stage 1.
- `modules/efps-inventory-mgmnt/src/inventory_runtime.py` as the live Stage-1 durable intake adapter. It owns session capture/deduplication and delegates closed-session processing to the canonical `pipeline.process_closed_session()` implementation.
- `handler.py` as the scheduled Raw-row worker using only the canonical Inventory package.
- The SAM live-integration boundary, including the DynamoDB session-table ARN needed by the Stage-1 adapter.

## CRM reconciliation state — 2026-09-26

Canonical CRM documentation is under `docs/crm/`; the two dated audits are preserved under `docs/audits/`.

Reconciled:
- `efps-internal-automatios` is the canonical CRM implementation repository.
- D01–D04 remain approved; D05 is proposed and informed by the verified Housing Listings audit.
- Figma is the working design environment; Canva remains the visual reference.
- Housing Inventory is the live `Housing_Listings` Google Sheet under the 48-field repository contract.
- Inventory Stage-1/2 write boundary is A:D and F:AO; AU/AV are reserved and blank.
- The legacy lead extraction, legacy `leads.db`, and Leads Tracker (`1GfM9lPQSukVpxCEVUlUDxFj_WYg0xQj8Inn7FA4sLVI`) are historical evidence layers. They are not the current CRM lead write/read path. Current production CRM ingress is WhAPI → `crm_webhook_events` → Supabase CRM tables; the canonical inventory Sheet is the separate `Housing_Listings` workbook.
- The current audit reports are evidence snapshots, not permission to mutate production data.

Open blockers are maintained in `docs/OPEN_POINTERS.md`.

Next ordered stage after this reconciliation branch: correct the approved Figma screens and design/approve D05. Implementation and Render deployment follow only after the UI design gate.

## Remaining external dependencies

These are future live-runtime verification tasks, not unresolved Phase-1 implementation defects:

- Slack app installation, bot membership, command registration, deployed endpoint/signature verification, and live API probe.
- Exact `inventory_locked` live Sheet control vocabulary.
- Google Maps network resolution after deterministic URL extraction.
- WhAPI live transport verification, including whether the observed diagnostic-required `User-Agent: EFPS-Inventory-Phase1/1.0` should be made mandatory in the shared client.

## Current Slack command surface

**Production-grade (5):**
- `help` — usage guide
- `status` — system status
- `show <listing_id>` — property details
- `assign <listing_id>` — retry collection assignment
- `run` — manual lead worker trigger (Lambda invocation)

**Functionally hardened (4):**
- `add-property` — new property intake
- `photos start` — photo collection workflow
- `catalogue start` — catalogue image management
- `catalogue update` — catalogue update workflow

**Known behaviour:** WhAPI returns `{"error": "operation_timeout"}` as an HTTP 200 on the PATCH `/business/collections/{id}` endpoint when its backend is slow. `assign_to_collection` now detects this and retries once with the same 10s backoff used for 429.

**Removed commands:** `/efps fix` and `/efps verify` removed 2026-09-21. Properties requiring corrections should be edited directly in the Sheet or through future admin tools.

## Active CRM UI handoff — 2026-09-30 (supersedes historical CRM-reconciliation-only heading)

- CRM UI implementation/deployment is on `crm-ui-dashboard`; repository `main` is reconciled to the approved CRM checkpoint but is not the Render deployment branch.
- Render `easyfind-crm-d01-d05` successfully called hosted Ollama `gpt-oss:20b` with fictional `L-1001` at 2026-09-26 21:25:38 UTC. The five expected keys were returned. No local model.
- Dedicated root `steering.md` is the only CRM model system instruction, loaded and cached by `src/ollama-adapter.mjs` (2-KiB maximum). It conveys EFPS brokerage purpose, model role, structured extraction, operator control and no invented facts. Repository `CORE_STEERING.md` remains separate.
- Application tests, build, browser and GitHub Actions must pass on the new steering commit; Render `49b4f30` succeeded with the dedicated steering at 2026-09-26 21:36:16 UTC. Optional `CRM_OLLAMA_STARTUP_SMOKE_ENABLED=false` is deployed: `dep-das3lspa4omc738mqre0` live at 2026-09-26 21:37:57 UTC; no startup inference observed. On-demand fictional pilot remains enabled.
- Current production Supabase state contains reconciled real CRM data for `+919148338801`; historical records and live webhook events use the same source-aware reconciliation path. D06 and D07 are resolved; D08 remains the final visual-system/handoff item. Independent encrypted backup + isolated restore proof remains a separate infrastructure hardening item.

## 2026-09-27 — CRM UI branch reconciliation

- `crm-ui-dashboard` is the canonical CRM UI dashboard and deployment branch. Render currently deploys this branch; local and GitHub state are reconciled to the same commit.
- Current production source for this CRM deployment is WhatsApp `+919148338801`. Historical records and live webhook events are reconciled through Supabase before appearing as CRM data.
- The other configured WhatsApp source numbers remain visible in the UI for future onboarding but are not part of the current production import scope.
- Render currently tracks `crm-ui-dashboard`; do not repoint this CRM UI deployment to `main` as part of the current production flow.
- The CRM UI working checkout is `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/crm-ui-dashboard`, tracking `origin/crm-ui-dashboard`. Keep the historical `leads_automation/leads-ui` application separate.
- Source-scoped real-data migration for the current source is complete. Independent backup/restore proof and D08 remain open; D06/D07 are resolved. These items do not disable the current `+919148338801` production flow.

## CRM daily workflow — 2026-09-30

The approved CRM interaction model is deliberately simple:

1. Open Dashboard and review the four daily counters.
2. Open Contact Classification for contacts not yet promoted.
3. Select one classification and click Update.
4. Non-qualified contacts remain in Not pushed to CRM.
5. Qualified Lead moves the contact to Qualified leads pushed to CRM only after the Supabase transaction succeeds.
6. Open the next item from Today's follow-ups and continue work from the lead workspace.
7. Follow-up history remains visible under the lead's Activity & History tab.

Do not add a separate classification filter or a second intake workflow unless this decision is explicitly revisited.


## 2026-10-01 — Browser and D07 handoff

Browser E2E now covers operator sign-in and the query-string-bearing live-record workspace route. D07 is resolved: session authentication, sensitive-data masking, explicit/reversible archive/restore, global audit visibility, export/retention/deletion boundaries, and offline/sync states are implemented. Activity is the global security/operator audit surface; Lead Workspace Activity & History remains lead-specific. D08 remains the final visual-system/handoff stage.

## 2026-10-01 — Leads Inbox usability checkpoint

Leads Inbox and Dashboard lead cards now expose Contacted date (first Incoming/customer message), Last message sent by (Customer or Us), and Last message date (latest stored message). Timestamps are displayed in Asia/Kolkata as DD-Month-YYYY / HH:MM. The protected API computes these values from crm_messages before pagination.

Inbox sorting is server-side: Last message newest, Customer replied newest, First contacted newest, Last message oldest, and Name A–Z. Browser coverage includes the timeline fields, sort request, and 900px compact/mobile layout.


## 2026-10-01 — Production AI + normalized requirements implementation

Implemented on `crm-ui-dashboard` and verified locally:
- Requirements are now a normalized one-row-per-lead table, `crm_lead_requirements`, with fixed inventory-matchable fields: BHK, budget, preferred locations, tenant type, move-in date, pets, veg/non-veg, furnishing, parking, property type, bathrooms, occupancy count, lease term, preferred floor, preferred amenities and notes. `lead_id`, timestamps and `updated_by` preserve relational/audit linkage. Legacy `crm_leads.requirements` remains a compatibility mirror, not the authoritative edit surface.
- Requirements are editable from Lead Workspace and persisted transactionally through the protected CRM server.
- AI is no longer synthetic-fixture-only. Production analysis receives the complete chronological lead conversation, normalized requirements, requirement evidence, operator notes, prior AI runs and a per-lead AI cursor.
- AI output contains summary/timeline, evidence-backed requirement proposals, missing information, contradictions, suggested lead status, reply strategy, reply draft and evidence. Lead status remains suggestion-only.
- Requirement proposals require explicit operator acceptance; acceptance updates the normalized requirement table and appends requirement evidence. Reject is also audited.
- Every lead has its own AI cursor; the workspace exposes AI run history, requirement evidence, proposal review, draft editor and draft history.
- AI reply drafts are versioned in `crm_drafts`. The operator can edit/save/copy/open WhatsApp; the CRM never auto-sends the draft.
- Root `steering.md` now contains production EFPS context and explicit rules for full-history analysis, cold-lead reactivation, requirement evidence, inventory truth and operator-only sending. Public EasyFind context is based on the official EasyFind Property Solutions site. (official site: https://www.easyfindprops.com/)
- Live Supabase verification after schema deployment: 186 requirement profiles, 186 per-lead AI cursors, 6,622 CRM messages (4,228 outgoing), 195 webhook events (195 processed, 0 failed). AI runs/drafts/evidence remain 0 until an operator first runs production AI and accepts/creates outputs.

## 2026-10-01 — Production activation and repository-wide documentation checkpoint

Render service `srv-darsv560tbcc73cu4ip0` is the production CRM dashboard service and deploys `crm-ui-dashboard`. Commit `6f5f3ea629fc1d26dfe0cef2d6b9602eb6a6ad0e` contains the normalized requirements and production AI workspace implementation. Render auto-deployed that commit; the subsequent environment merge enabled `CRM_REAL_AI_ENABLED=true` and `CRM_DB_WRITE_ENABLED=true` without replacing existing secrets.

Current production AI behavior: complete chronological lead conversation + normalized requirements + requirement evidence + operator notes + prior AI runs + per-lead cursor are supplied to the configured Ollama model. AI produces evidence-backed requirement proposals, a timeline/context summary, a suggested lead status, and an editable reply draft. Requirement changes require operator acceptance. Drafts are versioned. No AI-generated message is automatically sent to WhatsApp and lead status is suggestion-only.

Local evidence: `npm test` passed 63/63 tests and production build passed. A local authenticated server smoke confirmed the dashboard serves the operator sign-in route. Supabase verification after migrations showed 186 normalized requirement profiles and 186 per-lead AI cursors. Existing production message/webhook counts were also rechecked. The Render deploy for the environment activation is tracked separately by its Render deploy ID.

## 2026-10-01 — AI draft workspace crash/reload fix

A production operator run exposed a UI-state defect after successful AI inference: the AI run and draft were persisted, but the draft editor/history were only rendered while the in-memory `ai.proposal` state existed. After reload, the lead showed the saved AI run count but the saved draft was not accessible. The AI result path now restores the latest persisted draft into the editor, renders Draft workspace/history independently of transient AI state, makes saved draft versions clickable for loading/editing, and makes Open WhatsApp actually open the lead chat while recording the draft as opened. AI request failures now expose the server error instead of a generic blank state. A React error boundary was also added so an unexpected render error shows a reloadable CRM error surface rather than a blank screen. This preserves persisted AI/draft data and does not change the no-auto-send control.

Observed production lead workspace after the operator test run: 6 conversation messages, 2 saved AI runs and 2 saved draft versions. The Activity & History view also records `draft.created`, confirming persistence/audit survived the UI failure.

Local verification after the fix: `npm run build` passed and `npm test` passed 63/63; `git diff --check` passed. The Playwright browser regression command was retried but did not complete in the local environment during this checkpoint, so it is not claimed as passed for this fix.
