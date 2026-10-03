# Document Map

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

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The final repository verification was 78/78 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.



This document is the canonical map of maintained repository documentation. It tells future AI sessions where a fact, rule, decision, contract, or current-state update belongs.

## Root: AI/repository operation

| Document | Role |
|---|---|
| `README.md` | Human-oriented repository entry point |
| `CORE_STEERING.md` | Mandatory core AI operating protocol |
| `GEMINI.md` | Gemini CLI operating adapter and concise repository rules |
| `AGENTS.md` | General AI-agent operating rules and core-steering enforcement |
| `HANDOFF.md` | Current working state between sessions |

## `docs/`: business and system truth

| Document | Role |
|---|---|
| `BUSINESS_CONTEXT.md` | EFPS business rules, terminology, tone, and decision principles |
| `PROJECT_RULES.md` | Standing engineering and automation rules |
| `ARCHITECTURE.md` | Repository structure, boundaries, and established flows |
| `DATA_CONTRACTS.md` | Cross-module data ownership and contracts |
| `INFRASTRUCTURE.md` | External systems and verified resource identifiers; never secrets |
| `DOCUMENT_GOVERNANCE.md` | Document classes, authority, and maintenance governance |
| `DOCUMENT_MAP.md` | Maintained-document ownership map |
| `DOCUMENT_UPDATE_MATRIX.md` | Routing table for documentation review/update decisions |
| `OPEN_POINTERS.md` | Unresolved decisions and verified unknowns |
| `MIGRATION_LIVE_SYSTEM_MAP_20260916.md` | Approved live-system migration boundary and responsibility classification |
| `INVENTORY_SOURCE_EXTRACTION.md` | Canonical Stage-2 source segmentation and deterministic extraction contract |
| `DETERMINISTIC_FIELD_RESOLUTION.md` | Canonical candidate extraction/resolution/normalization contract for deterministic Stage-2 fields |
| `NEEDS_REVIEW_CONTRACT.md` | Blocking property-detail fields and deterministic `Needs Review` status contract |

## Local documentation

Every module and established shared capability has its own `README.md` explaining its purpose and boundary. Active implementation packages should also document their runtime requirements and validation approach locally.

Repository-wide Gemini skills live under `.gemini/skills/`. Repository-specific custom skills may have reference files under their skill directory when the procedure requires detailed material.

## Shared capabilities

Established shared capabilities include:

- `shared/cloudinary/`
- `shared/credentials/`
- `shared/google_maps/`
- `shared/google_sheets/`
- `shared/slack/`
- `shared/whatsapp_whapi/`

`shared/credentials/` is the canonical technical credential-provider boundary; credential values are never repository documentation.

### `shared/google_maps/` canonical documents

- `README.md` — capability boundary, authentication references, runtime behavior, resolution states, and verified Phase-1 acceptance.
- `CREDENTIALS.md` — non-secret Google Maps credential registry.
- `client.py` — reusable Maps API transport and normalized `MapsResolution` adapter.
- `test_google_maps.py` — unit coverage for credential precedence/fallback behavior.

### `shared/slack/` canonical documents

- `README.md` — capability boundary, topology, lifecycle and migration status.
- `COMMANDS.md` — supported `/efps` command surface and removed commands.
- `CHANNELS.md` — current and historical channel topology and routing.
- `SLACK_APP_MANIFEST.md` — cleaned Slack app manifest specification.
- `REVERIFY_PHOTOS.md` — photo recovery/re-verification reference.
- `PHASE1_BULK_PHOTOS.md` — exact current Phase-1 bulk-photo operator flow.
- `PROPERTY_VERIFICATION.md` — human property verification workflow.
- `BATCH_OPERATIONS.md` — batch controls, reports, review relationship and failure behavior.
- `NEW_USER_GUIDE.md` — practical EFPS Slack operations guide.
- `PHASE1_BOUNDARY.md` — Slack's Inventory Phase-1 scope and ownership boundary.
- `RELEASE_GATE.md` — production acceptance criteria for Inventory Phase 1.
- `IMPLEMENTATION_MAP.md` — legacy-to-new capability mapping and boundaries.
- `HANDOFF.md` — migration status and remaining activation work.
- `client.py` — reusable Slack Web API transport.
- `security.py` — inbound request signature verification.
- `safety.py` — safe text and thread-control helpers.
- `routing.py` — channel/workspace routing constants.

### Live-system migration document

`MIGRATION_LIVE_SYSTEM_MAP_20260916.md` is the single maintained map for the approved live-system migration. It records which capabilities are retained from current `main`, which live integration components are reconciled, and which legacy Inventory responsibilities are explicitly excluded.

## CRM documentation

The private EasyFind CRM has its canonical documentation under `docs/crm/`:

| Document | Role |
|---|---|
| `docs/crm/README.md` | CRM documentation index and current design/status boundary |
| `docs/crm/CRM_SOURCE_OF_TRUTH_RECONCILIATION.md` | Reconciled source hierarchy, conflicts, authority boundaries and blockers |
| `docs/crm/CRM_DATA_MODEL.md` | Canonical CRM/UI fields and physical source mappings |
| `docs/crm/CRM_CURRENT_VERIFIED_STATE.md` | Canonical current production/UI/DB/Render/Git checkpoint and flow/test history |
| `docs/crm/CRM_DETERMINISTIC_CLASSIFICATION.md` | Canonical deterministic classification rules, storage, scheduler, provenance and validation |
| `docs/crm/CRM_DESIGN_DECISIONS.md` | D00–D08 design decision register |
| `docs/crm/CRM_UI_DESIGN_SPEC.md` | UI information architecture and interaction rules |
| `docs/crm/LEAD_CRM_MASTER_PLAN.md` | CRM delivery sequence and implementation gates |
| `docs/audits/HOUSING_INVENTORY_SOURCE_OF_TRUTH_AUDIT.md` | Dated Housing Listings evidence snapshot |
| `docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md` | Dated Leads/WhatsApp extraction evidence snapshot |

The audit documents are historical evidence snapshots. The CRM reconciliation documents are the canonical current interpretation for this branch. They must not duplicate or silently overwrite the canonical cross-module contracts owned by `docs/DATA_CONTRACTS.md`, `docs/ARCHITECTURE.md`, and `docs/INFRASTRUCTURE.md`.

## Single-source rule

One fact or rule should have one canonical home. Other documents may link to or summarize it, but must not create a competing authoritative version.

For every implementation, the agent must review all maintained root and `docs/` documents. Update every document whose content is affected by resulting repository reality; documents not affected must still be checked for continued accuracy.

Presence of a shared capability boundary does not imply that every runtime feature is complete or live.

If a new maintained document is required, add it to this map and define its role before treating it as repository truth.

## CRM-only model instructions

| Document | Role |
|---|---|
| Root `steering.md` | Executable, compact, dedicated system instruction for the CRM hosted Ollama model; not repository-agent governance. Canonical business facts remain in `docs/BUSINESS_CONTEXT.md`. |
| `docs/crm/CRM_AI_AND_LEAD_IMPORT_GATE_2026-09-27.md` | Dated verification of hosted model, dedicated steering and remaining real-data gates. |

`src/ollama-adapter.mjs` loads only `steering.md` as model system context. Repository agents must still follow `CORE_STEERING.md`; the hosted model does not receive it.
