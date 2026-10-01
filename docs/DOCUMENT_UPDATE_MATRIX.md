# Documentation Update Matrix

## Current verified repository state — 2026-10-01

This section is the current checkpoint for maintained documentation. Dated audit sections below remain historical evidence and are not silently rewritten.

- **Canonical UI/deployment branch:** `crm-ui-dashboard`
- **`crm-ui-dashboard` commit:** `da13083f6cb1f3c78ec3f4df661c515d43f556fa`
- **`crm-ui-dashboard` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **`main` reconciliation commit:** `692bdcbbab51752b8eb7d4927921d1cfc4830de7`
- **`main` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**; commit histories differ by design.
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, deployment `dep-dav55km0tbcc73eelat0`, **live**.
- **Production source:** `+919148338801`.
- **Supabase CRM:** 186 leads; 307 classifications; 20 pending; 186 promoted; 6,853 messages; 436 webhook events, 436 processed, 0 received, 0 processing, 0 failed.
- **AI persistence:** 196 AI runs, 196 proposed; 196 drafts; 186 AI cursors.
- **Inventory:** 88 active Housing rows; 1,333 sync-run records; latest recorded sync = 88 rows / 0 changed / 0 removed; AU/AV remain outside the CRM operational A:AT mirror.
- **Schedulers:** `crm_webhook_reconcile_1m` active every minute; `crm_inventory_sheet_reconcile_5m` active every five minutes.
- **P1–P5:** implemented and production-verified as documented in `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.
- **Verification:** `npm run build` PASS; `npm test` PASS (71/71); `npm run test:browser` PASS (1/1).
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



**Status:** Active baseline  
**Purpose:** Define which maintained documents must be reviewed or updated when repository reality changes.

> This matrix is a routing guide. It does not replace `CORE_STEERING.md` or `DOCUMENT_GOVERNANCE.md`.

| Change type | Mandatory document review/update |
|---|---|
| Core AI operating protocol changes | `CORE_STEERING.md`, `AGENTS.md`, `GEMINI.md`, affected AI skills |
| General AI-agent governance changes | `AGENTS.md`, and `CORE_STEERING.md` if core protocol is affected |
| Gemini workflow/operating changes | `GEMINI.md`, affected Gemini skills |
| Current task/session state changes | `HANDOFF.md` |
| Repository structure changes | `docs/ARCHITECTURE.md`, root `README.md`, `docs/DOCUMENT_MAP.md`, affected local README/GEMINI files |
| Business rule/context changes | `docs/BUSINESS_CONTEXT.md` |
| Engineering/governance rule changes | `docs/PROJECT_RULES.md` |
| Architecture/boundary changes | `docs/ARCHITECTURE.md`, `docs/DATA_CONTRACTS.md` when contracts/ownership are affected |
| Data ownership/schema/contract changes | `docs/DATA_CONTRACTS.md` |
| Infrastructure/resource changes | `docs/INFRASTRUCTURE.md` |
| Credential-provider or credential-reference changes | `docs/INFRASTRUCTURE.md`, affected shared capability credential registry/README, `HANDOFF.md`, and `docs/OPEN_POINTERS.md` when verification state changes |
| New unresolved decision/unknown/conflict | `docs/OPEN_POINTERS.md` |
| Documentation structure/role changes | `docs/DOCUMENT_GOVERNANCE.md`, `docs/DOCUMENT_MAP.md` |
| Module responsibility/behavior changes | Relevant module `README.md` and `GEMINI.md`; canonical docs when cross-module truth changes |
| Shared capability responsibility/behavior changes | Relevant shared `README.md`; canonical docs when cross-cutting truth changes |
| Inventory source-extraction behavior changes | `docs/INVENTORY_SOURCE_EXTRACTION.md`, `docs/DETERMINISTIC_FIELD_RESOLUTION.md`, `docs/ARCHITECTURE.md`, `docs/DATA_CONTRACTS.md`, Inventory module `README.md`, affected regression fixtures, `HANDOFF.md` |
| Inventory validation/normalized-storage contract changes | `docs/DATA_CONTRACTS.md`, `docs/DETERMINISTIC_FIELD_RESOLUTION.md`, `docs/PROJECT_RULES.md`, Inventory module `README.md`, affected validation/regression tests, `HANDOFF.md` |
| Inventory model-audit/reporting behavior changes | `docs/DETERMINISTIC_FIELD_RESOLUTION.md`, `docs/DATA_CONTRACTS.md`, Inventory module `README.md`, `HANDOFF.md`, affected test tooling |
| Repository overview changes | root `README.md` |
| CRM current verified state checkpoint | `docs/crm/CRM_CURRENT_VERIFIED_STATE.md`, `HANDOFF.md`, `docs/INFRASTRUCTURE.md`, `docs/OPEN_POINTERS.md`, affected CRM docs |
| CRM data-source/schema reconciliation | `docs/crm/CRM_SOURCE_OF_TRUTH_RECONCILIATION.md`, `docs/crm/CRM_DATA_MODEL.md`, `docs/DATA_CONTRACTS.md`, `docs/OPEN_POINTERS.md`, `HANDOFF.md` |
| CRM design decision/status changes | `docs/crm/CRM_DESIGN_DECISIONS.md`, `docs/crm/CRM_UI_DESIGN_SPEC.md`, `docs/crm/LEAD_CRM_MASTER_PLAN.md`, affected Figma handoff references, `HANDOFF.md` |
| CRM prototype repository/runtime changes | `docs/crm/LEAD_CRM_MASTER_PLAN.md`, `docs/crm/CRM_UI_DESIGN_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/INFRASTRUCTURE.md`, `HANDOFF.md` |
| Repository-wide AI skill changes | `.gemini/skills/README.md`, affected skill, relevant governance docs |
| Repository-specific custom skill changes | `.gemini/skills/README.md`, affected skill and references, relevant capability/module docs |

| CRM hosted-model prompt/steering change | Root `steering.md`, `src/ollama-adapter.mjs`, `tests/ollama-adapter.test.mjs`, `docs/crm/CRM_AI_AND_LEAD_IMPORT_GATE_2026-09-27.md`, `docs/crm/LEAD_CRM_MASTER_PLAN.md`, `docs/crm/CRM_RENDER_CONFIGURATION.md`, `HANDOFF.md`; update `docs/BUSINESS_CONTEXT.md` only when business truth actually changes. |

## Mandatory agent behavior

For **every implementation**, the agent must review **all maintained root documents and all documents inside `docs/`** against the resulting repository reality. It must update every document that is affected and must confirm the remaining documents are still accurate. This full review is mandatory even when the change appears small.

For a shared capability implementation, review the capability's local `README.md`, relevant capability code/tests, and the canonical architecture, contracts, infrastructure, and open-pointer documents.

For all other maintained documentation, use the routing table above to identify additional local documents that must be reviewed or updated.

If the matrix does not clearly cover a change, do not guess. Establish the correct documentation owner before proceeding and update this matrix if a durable routing rule is discovered.

## Maintenance

This matrix is the canonical routing baseline. It must be refined when actual implementation reveals a new durable document owner or recurring update pattern.


## CRM production checkpoint 2026-09-30

The current CRM production truth is maintained in `docs/crm/LEAD_CRM_MASTER_PLAN.md`, `docs/crm/CRM_UI_BRANCH_RECONCILIATION.md`, `docs/crm/CRM_LIVE_WHAPI_WEBHOOK.md`, `docs/crm/CRM_DATA_MODEL.md`, and `HANDOFF.md`. These documents supersede older synthetic-only or pre-WhAPI gate statements while retaining those dated documents as historical evidence.
