## Authoritative current repository state — 2026-10-02

- **CRM implementation branch:** `crm-ui-dashboard`
- **Current CRM dashboard commit:** `c53183d4da1bfc9a36eda55ddf92da87b48dabe9`
- **Reconciliation commit on `main`:** `4266693e10144987c6fcc3ffd3dddf88511144cf`
- **Repository tree state:** `main` and `crm-ui-dashboard` are synchronized to the same file tree; no force-push or history rewrite was used.
- **Recovered UI work:** classification visibility/tone, overdue follow-up attention, inventory sorting/filtering/pagination, stale-response protection, classification pagination reset, responsive/accessibility regression coverage.
- **Replit-only workspace artifacts:** excluded from the synchronized tree.
- **Production dependency manifest:** restored to the verified baseline.
- **Production backend boundary:** WhatsApp/WhAPI ingestion, Supabase persistence/reconciliation, CRM promotion/classification, AI/drafts, inventory synchronization, authentication, privacy, audit, archive/restore and exports were not intentionally altered by the UI reconciliation.
- **Render source branch:** `crm-ui-dashboard`.
- **Deployment status:** the dashboard branch has been updated and therefore the configured Render auto-deploy path has been triggered. Render live-deployment verification remains an external runtime check; repository reconciliation itself is verified.

## 2026-10-02 — Replit feedback branch recovery and line-by-line audit checkpoint

The isolated branch `crm-ui-feedback-polish-2026-10-02` was recovered after the Replit workspace exhausted its credits. The branch is based directly on production checkpoint `97b43a7d158eb8b3cd773ed3febb45c4f8a52540` and contains the recovered UI/inventory implementation plus regression coverage.

### Audited implementation extracted for verification

- Lead cards now expose persisted `crm_leads.classification` separately from operational `crm_leads.lead_type`; missing classification is rendered as `Not recorded` and is not inferred from age, message history, budget, or AI output.
- Lead cards expose a persisted overdue-follow-up count derived from incomplete follow-ups whose due time has passed. No financial-risk label is inferred from budget.
- Lead status tones are secondary, low-contrast semantic styling and remain text-labelled; color is not the only meaning.
- Lead-card classification spacing and mobile hierarchy were hardened with explicit identity-to-classification separation and narrow-screen overflow coverage.
- Inventory KPI cards remain clickable and use full-inventory summaries/facets rather than page counts.
- Inventory search, status/BHK/locality/photo filters, sorting, and 24-row pagination now compose through the protected inventory overview response. Filter/sort changes reset to page zero; the browser ignores stale inventory/audit responses.
- Inventory pagination has explicit query validation and deterministic filter/sort/page regression coverage.
- Global and lead Activity requests use cancellation guards so stale responses cannot overwrite current state.
- Contact Classification filter/source changes reset pagination without issuing a stale page response.
- Browser regression coverage now exercises inventory page 2, filter reset, classification visibility, overdue attention, mobile classification spacing, and horizontal-overflow safety.

### Audit exclusions / corrections

- Replit-only `.replit` and startup-instruction asset were removed from the promotion candidate.
- Replit-mutated dependency ranges and package-firewall lockfile URLs were removed; the production `package.json` and `package-lock.json` were restored to the verified `97b43a7` baseline.
- No production database write, webhook/integration change, schema migration, or Render deployment is included in this checkpoint.

### Verification state

Implementation review is complete at the repository diff level. Build, full automated tests, browser regression, production deployment, and branch reconciliation remain evidence-gated until the recovered candidate is executed and verified. This section must not be interpreted as a production-live claim.

## Unreleased CRM UI feedback branch checkpoint — production unchanged

The requested UI polish is isolated on `crm-ui-feedback-polish-2026-10-02`; it has not been merged or deployed. This branch keeps stored classification separate from lead status, shows only persisted overdue follow-up attention, and paginates the filtered/sorted inventory response server-side while retaining full-inventory KPI totals and facets. No production data, CRM integrations, schema, or write behavior has been changed. Local check results and any runtime caveat will be recorded here after verification.

## Authoritative current CRM UI verification — 2026-10-02

This is the current production checkpoint after the audited CRM UI polish, routing hardening, verification, deployment, and repository reconciliation. Older dated sections remain historical evidence.

- **CRM deployment branch:** `crm-ui-dashboard`
- **Application/UI merge commit:** `7911ef574c98610063f0069e738c06b40fd911b2`
- **Production deployment:** the verified UI release is live on the production Render service from `crm-ui-dashboard`
- **Production health:** live fetch of `/health` returned HTTP 200 with `{"ok":true}`
- **Automated verification:** GitHub Actions run #22 passed `npm run build`, `npm test` (84/84), and `npm run test:browser` (1/1) on Node.js 24.21.0 for the verified application candidate. A later documentation-state verification run also passed.
- **Implemented:** stable direct CRM routes and lead deep links; browser-history and lead-tab routing; debounced lead search; restored desktop layout foundations; consolidated UI polish; responsive/mobile behavior; accessibility states; inventory presentation/filtering/sorting surfaces; route/browser regression coverage.
- **Production boundary:** no backend source or API-contract changes were introduced by this UI release. Webhook ingestion/reconciliation, Supabase persistence, classification, AI, inventory data logic, authentication, privacy, and audit backend paths were preserved.
- **Runtime:** Node.js 24.21.0 is explicitly pinned through `.node-version` and package engine constraints; this matches the current Render Node 24 default documented for services created on or after 2026-09-17.
- **Replit defects resolved:** the accidental terminal-output file and Replit-only `.replit` configuration were not carried into the production tree; the deleted desktop CSS foundation was reconstructed from the verified production baseline.
- **Repository state:** `tree(main) == tree(crm-ui-dashboard)` is verified after the final repository reconciliation. No force-push or history rewrite was used on `main`.

## Authoritative current verified state — 2026-10-01 21:55 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **CRM commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **CRM tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **main:** `b2fbf366021852aedd4bf0ec66484ad421fb5662`
- **main tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
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


# Current verified handoff — 2026-10-01

> Historical checkpoint: the earlier audit snapshot is retained below for evidence. The authoritative current state is the 2026-10-01 21:55 IST checkpoint at the top of this file.

## Unreleased Inventory/UI hardening in crm-ui-dashboard

The safe working tree includes an Inventory release that makes all four inventory KPI cards clickable filters, adds validated inventory sorting via the inventory_sort query contract (Latest, Oldest, rent low/high, BHK low/high, Locality A–Z), and hardens Cloudinary/source media handling. Media values are normalized across arrays, direct URLs, object records, JSON strings, and delimited strings; card images lazy-load with explicit failure/retry states.

The release also hardens operator interactions: buttons declare their intended type, navigation exposes active state, offline writes/exports are disabled, failed durable actions surface a visible error, and failed lead field writes refresh from the server rather than leaving an optimistic value.

Production data audit during this work: 88 active Housing mirror rows; 83 have non-empty Cloudinary image URL arrays and 5 do not; sampled production Cloudinary URLs returned HTTP 200 image/jpeg. No database data was modified by the UI hardening.

Validation: npm run build PASS; npm test PASS (74/74); npm run test:browser PASS (1/1). Main checkout was not modified; work is isolated to the crm-ui-dashboard clone.


## Previous release metadata

Historical release metadata is retained below; see the authoritative current-state block above.

Historical dated sections below remain evidence snapshots and must not be interpreted as the current checkpoint.

## CRM production checkpoint — 2026-09-30

Historical checkpoint retained below.


## Current state

## Current production checkpoint — 2026-10-01

Historical production checkpoint retained below; see the authoritative current-state block above.

The Leads Inbox card surface is simplified to lead status + source number. The inbox header exposes live clickable counts for all lead statuses and clicking a status applies the server-side filter. AI draft runs persist provider usage metrics (input/output/total tokens and estimated USD cost where pricing is known) alongside model/provider provenance. Complete conversation history remains authoritative; incremental/delta analysis is intentionally not implemented.

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
4. Non-qualified contacts remain in Waiting for classification.
5. Qualified Lead moves the contact to Total active inventory to CRM only after the Supabase transaction succeeds.
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
- Live Supabase verification after schema deployment: 186 requirement profiles, 186 per-lead AI cursors, 6,622 CRM messages (4,228 outgoing), 195 webhook events (195 processed, 0 failed). That initial post-deployment checkpoint had no AI runs/drafts yet; the current live database now contains 2 AI runs and 2 drafts for the tested lead, both generated by the Ollama fallback-era runs.

## 2026-10-01 — Production activation and repository-wide documentation checkpoint

Render service `srv-darsv560tbcc73cu4ip0` is the production CRM dashboard service and deploys `crm-ui-dashboard`. Commit `6f5f3ea629fc1d26dfe0cef2d6b9602eb6a6ad0e` contains the normalized requirements and production AI workspace implementation. Render auto-deployed that commit; the subsequent environment merge enabled `CRM_REAL_AI_ENABLED=true` and `CRM_DB_WRITE_ENABLED=true` without replacing existing secrets.

Current production AI behavior: complete chronological lead conversation + normalized requirements + requirement evidence + operator notes + prior AI runs + per-lead cursor are supplied to the configured Ollama model. AI produces evidence-backed requirement proposals, a timeline/context summary, a suggested lead status, and an editable reply draft. Requirement changes require operator acceptance. Drafts are versioned. No AI-generated message is automatically sent to WhatsApp and lead status is suggestion-only.

Local evidence: `npm test` passed 63/63 tests and production build passed. A local authenticated server smoke confirmed the dashboard serves the operator sign-in route. Supabase verification after migrations showed 186 normalized requirement profiles and 186 per-lead AI cursors. Existing production message/webhook counts were also rechecked. The Render deploy for the environment activation is tracked separately by its Render deploy ID.

## 2026-10-01 — AI draft workspace crash/reload fix

A production operator run exposed a UI-state defect after successful AI inference: the AI run and draft were persisted, but the draft editor/history were only rendered while the in-memory `ai.proposal` state existed. After reload, the lead showed the saved AI run count but the saved draft was not accessible. The AI result path now restores the latest persisted draft into the editor, renders Draft workspace/history independently of transient AI state, makes saved draft versions clickable for loading/editing, and makes Open WhatsApp actually open the lead chat while recording the draft as opened. AI request failures now expose the server error instead of a generic blank state. A React error boundary was also added so an unexpected render error shows a reloadable CRM error surface rather than a blank screen. This preserves persisted AI/draft data and does not change the no-auto-send control.

Observed production lead workspace after the operator test run: 6 conversation messages, 2 saved AI runs and 2 saved draft versions. The Activity & History view also records `draft.created`, confirming persistence/audit survived the UI failure.

Local verification after the fix: `npm run build` passed and `npm test` passed 63/63; `git diff --check` passed. The Playwright browser regression command was retried but did not complete in the local environment during this checkpoint, so it is not claimed as passed for this fix.


## 2026-10-01 — AWS Bedrock primary AI provider

The local Mac AWS configuration was verified against account `294417174793` in `ap-southeast-2`. Anthropic model availability was checked with Bedrock `GetFoundationModelAvailability`. The account currently has completed model agreement/authorization/entitlement for five Anthropic models: Claude Haiku 4.5, Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Opus 4.6, and Claude Opus 4.5. Other listed Anthropic models were not selected because their agreement status is not available in this account.

The CRM AI provider order is now **AWS Bedrock → Ollama fallback**. The selected primary is **Claude Opus 4.6** using the APAC geographic inference profile `au.anthropic.claude-opus-4-6-v1`. This preserves the existing full-conversation steering/JSON contract and does not change operator approval or no-auto-send behavior. Bedrock uses the AWS SDK default credential chain; Ollama remains the fallback path.

Verified account quota values relevant to the enabled models include: Claude Opus 4.6 cross-region 25 RPM / 3,000,000 TPM; Claude Sonnet 4.6 50 RPM / 6,000,000 TPM; Claude Sonnet 4.5 50 RPM / 5,000,000 TPM; Claude Haiku 4.5 50 RPM / 5,000,000 TPM. Claude Opus 4.5 had 25 RPM global cross-region and 2,000,000 TPM global cross-region observed in the account quota pages. AWS documents that runtime TPM counts input and output together and that model-specific RPM/TPM values are enforced per model/region. The account-specific quota values take precedence over AWS published defaults.

A real local Bedrock Converse invocation against `au.anthropic.claude-opus-4-6-v1` succeeded with a 20-token test call, proving the configured AWS credentials can invoke the selected primary model. The production Render service has non-secret Bedrock configuration set to `AWS_REGION=ap-southeast-2`, `AWS_BEDROCK_MODEL_ID=au.anthropic.claude-opus-4-6-v1`, `AWS_BEDROCK_MAX_TOKENS=4096`, and `AWS_BEDROCK_TEMPERATURE=0.2`. Render now has AWS credentials configured as protected secrets. The current credential is the operator-approved temporary broad `all-access-user` identity; rotate it to a dedicated least-privilege Bedrock runtime identity before long-term production use. The Mac's local AWS profile is not inherited by Render.

## 2026-10-01 — Final current-state checkpoint
Render srv-darsv560tbcc73cu4ip0 is live from the reconciled crm-ui-dashboard deployment; the exact current commit is recorded in the final checkpoint below. Startup verified database/auth/Ollama/Sheets/Bedrock configuration presence and Supabase connectivity. AWS credentials are Render secrets and are not stored in Git.

## 2026-10-01 — Draft persistence/provenance checkpoint

The previously observed `View / edit` defect had a specific state-model cause: clicking a saved draft only changed `draftBody`, while the editor itself lived under transient `ai?.proposal` state. After a reload there was no transient proposal, so the click could not produce a visible editor even though the draft was persisted. The UI now renders the durable Draft workspace independently of transient AI state, explicitly selects a saved version, and exposes the saved body in a persistent editor. Each draft now stores `ai_run_id`, `ai_provider`, and `model_name`; existing two drafts were backfilled to their corresponding Ollama AI runs. New Bedrock-generated drafts will display the exact model/inference-profile identifier and provider.

Production database migration 16 (`016_crm_draft_ai_provenance.sql`) is applied and verified. Current live database result: 2 drafts, 2 identified draft models, 2 Ollama-era drafts, 0 Bedrock drafts so far. A future production AI run will provide the first live Bedrock-provenance draft after the Render credential configuration is exercised by the AI route.

## 2026-10-01 — AI generation hardening / model audition

Production lead `+919108474861` was verified in Supabase with three drafts: v1/v2 from `gpt-oss:20b`, and v3 from `au.anthropic.claude-opus-4-6-v1`. The v3 draft is the reference tone approved by the operator: concise apology/accountability, exact verified requirement, re-engagement question, and three targeted missing details without inventory claims.

A direct Bedrock tone audition was run against the same lead facts. `au.anthropic.claude-sonnet-4-6` produced a strong fallback candidate; `au.anthropic.claude-sonnet-4-5-20250929-v1:0` and Haiku 4.5 were also invokable but introduced less suitable phrasing/unsupported option language in the audition. `global.anthropic.claude-opus-4-5-20251101-v1:0` was invokable and produced a strong draft, but AWS documents Opus 4.5 without an AU geo inference profile, so Sonnet 4.6 is used as the production Bedrock fallback to preserve the existing AU routing. AWS documents Sonnet 4.6 as a 1M-context reasoning model and provides the `au.anthropic.claude-sonnet-4-6` profile.

The approved six AI improvements are implemented: stale-draft detection; provenance; evidence attached to drafts; deterministic pre-send grounding/safety checks; explicit copied/opened/sent outcome tracking; and explicit primary/fallback visibility. Incremental message/delta analysis is intentionally not implemented yet.

## 2026-10-01 — Final verified checkpoint after AI hardening

- Historical release metadata; see the authoritative current-state block at the top of this file.
- `crm-ui-dashboard` final tree: `7bce9e42ccd4efa9d14d85bbba8767961943aab0`.
- Render service `srv-darsv560tbcc73cu4ip0` is live from that commit; deployment `dep-dautgos9v7es73bnc44g` reached `live` and startup/database connectivity were verified.
- Historical reconciliation metadata; current main is reconciled to the crm-ui-dashboard tree.
- `main` tree equals `crm-ui-dashboard` tree: `7bce9e42ccd4efa9d14d85bbba8767961943aab0`.
- Local `crm-ui-dashboard` checkout equals `origin/crm-ui-dashboard` at `c19e36c...` and is clean.
- Production migration 17 is applied. Current database counts: 3 AI runs (2 Ollama, 1 Bedrock), 3 drafts, all 3 with source evidence; no `confirmed_sent` outcomes yet.
- Historical test checkpoint; current verification is build PASS, 78/78 automated tests, browser 1/1.
- GitHub combined-status API currently reports no status contexts for the final CRM/main commits; repository verification therefore relies on the local test suite, Git tree equality, Render deployment logs, health endpoint, and Supabase migration/data verification.

## 2026-10-01 — Bedrock SDK security update

Render's build surfaced dependency advisories through the newly added AWS Bedrock SDK, including a critical `fast-xml-parser` advisory in the older transitive tree. The Bedrock runtime SDK was upgraded from `3.922.0` to `3.1144.0`. Local `npm audit --omit=dev` now reports 0 vulnerabilities, and the full automated suite remains 66/66. The updated lockfile is part of the final repository state.

## Final 24-item CRM closure — 2026-10-01

Final current-state evidence is maintained in the authoritative block at the top of this file; current Cloudinary result is 829/829 successful direct HEAD checks.

## 2026-10-02 — UI/audit closure checkpoint

The current Lead Workspace implementation removes the redundant Actual lead badge and the one-time bulk-import Priority · Medium UI chip, uses the normalized requirements table with controlled enum values, separates explicitly evidenced property conversations from general messages, and labels the dashboard inventory KPI as Total available inventory.

Audit scope is now explicit: the global Activity page is CRM-wide and reads all crm_activity events; Lead Workspace Activity & History uses the same event table with lead_id scoping. Both support date ranges and pagination. This is one audit/event model with different UI scopes, not two independent histories.

Local verification for this checkpoint: npm run build PASS; npm test 79/79 PASS; npm run test:browser 1/1 PASS; git diff --check PASS. Deployment verification is required before this checkpoint is called production-live.

## 2026-10-02 — Final recovered-candidate audit record

- Candidate branch: `crm-ui-feedback-polish-2026-10-02`
- Candidate HEAD: `1241b062dfbc7a96b139ec0a7f68d68f43baab51e`
- Production/dashboard baseline: `97b43a7d158eb8b3cd773ed3febb45c4f8a52540`
- Pull request: #60 — CRM UI feedback polish
- Replit-only workspace artifacts removed before promotion.
- Production dependency manifest and lockfile restored to the verified baseline.
- Recovered implementation includes classification visibility/tone, overdue follow-up attention, inventory filtering/sorting/pagination, stale-response guards, classification pagination reset, and browser/server regression coverage.
- No production merge, Render deployment, database mutation, schema migration, or webhook/integration change has been performed from this candidate.
- Automated build/test evidence for this exact candidate is still pending; do not mark the candidate production-verified until `npm run build`, `npm test`, and `npm run test:browser` are observed passing.
- `main` and `crm-ui-dashboard` remain unchanged from the verified production baseline until that evidence gate is satisfied.


## 2026-10-02 final branch synchronization

`main` and `crm-ui-dashboard` now point to the same commit and identical repository tree. Current synchronized commit: `ca396f09fbb12c6871a36c1ab4436390338c6f74`. The dashboard branch was fast-forwarded to the reconciled main commit; no force-push or history rewrite was used.
