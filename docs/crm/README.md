# EasyFind CRM Documentation

## Authoritative current verified state — 2026-10-03 20:26 IST

Older dated checkpoints below are historical evidence and are not current-state declarations.

- Deployment branch: crm-ui-dashboard
- Render: easyfind-crm-d01-d05 / srv-darsv560tbcc73cu4ip0
- Supabase: qttcutwzehtskfcwxkwj
- Production source: +919148338801
- Current snapshot: 228 leads; 7,746 messages; 1,471 webhook events; 277 AI runs; 214 drafts; 354 classifications; 88 active inventory listings.
- Classification status: 228 promoted; 88 classified; 27 excluded; 11 pending.
- Group Message is a first-class Unqualified classification for pending webhook contacts whose chat_id ends in @g.us.
- The group rule is implemented in both webhook execution paths, audited, and the 14 currently pending group-originated contacts have been backfilled.

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
