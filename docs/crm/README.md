# EasyFind CRM Documentation

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



## Canonical working branch

`crm-ui-dashboard`

## Source hierarchy

**Leads:** the local extraction source defined by `docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md`. The local SQLite dataset produced by that extraction is the only lead dataset used by this CRM.

**Inventory:** verified Housing Listings contract/audit for property facts and D05.

## Documents

- `CRM_SOURCE_OF_TRUTH_RECONCILIATION.md` — current reconciled source and architecture boundary
- `CRM_DATA_MODEL.md` — canonical CRM/UI fields
- `CRM_DESIGN_DECISIONS.md` — D00–D08 decision register
- `CRM_UI_DESIGN_SPEC.md` — UI behavior
- `LEAD_CRM_MASTER_PLAN.md` — delivery sequence and gates

The two audit reports under `docs/audits/` are dated evidence snapshots. The leads audit is the authoritative source document for the local lead dataset.

## Approved design state

D01–D05 are approved, D06 is resolved, D07 is resolved, and D08 remains unresolved.

## Historical prototype boundary

The original prototype was synthetic-only. That dated boundary is retained for historical context; the current CRM production path uses source-scoped Supabase data for `+919148338801`. Automatic WhatsApp sending remains disabled, and inventory remains read-only from the CRM.

## CRM AI-specific steering

`steering.md` at repository root is the **dedicated, executable system prompt** for the hosted CRM Ollama adapter. It is deliberately distinct from the repository agent protocol `CORE_STEERING.md` and from canonical business facts in `docs/BUSINESS_CONTEXT.md`. Its limited EFPS context is loaded server-side and cached once per process; the fictional pilot remains the only authorized model input. See `CRM_AI_AND_LEAD_IMPORT_GATE_2026-09-27.md` for the verified hosted response and remaining data-import gates.


## 2026-10-01 — Current production closure status

The CRM browser regression is fixed and D07 is resolved on `crm-ui-dashboard`. D07 covers operator session security, sensitive-data masking, reversible archive, audit visibility, explicit export controls, retention/deletion boundaries and offline handling. D08 remains open.

## 2026-10-01 production AI checkpoint

The CRM AI workspace is now production-enabled on Render service `srv-darsv560tbcc73cu4ip0`. It analyzes the complete stored conversation and lead context rather than fictional fixtures. Requirements are normalized and editable in the Lead Workspace. AI proposals include evidence-backed requirement changes, timeline/context analysis, a suggested lead status, and a versioned reply draft. The AI does not automatically send WhatsApp messages.
