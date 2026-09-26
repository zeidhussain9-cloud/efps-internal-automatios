# EasyFind CRM Documentation

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

D01, D02, D03, D04 and D05 are approved. D06–D08 remain unresolved.

## Prototype boundary

Synthetic data only. No live customer data, live WhatsApp sending, destructive Sheets sync, or production writes.

## CRM AI-specific steering

`steering.md` at repository root is the **dedicated, executable system prompt** for the hosted CRM Ollama adapter. It is deliberately distinct from the repository agent protocol `CORE_STEERING.md` and from canonical business facts in `docs/BUSINESS_CONTEXT.md`. Its limited EFPS context is loaded server-side and cached once per process; the fictional pilot remains the only authorized model input. See `CRM_AI_AND_LEAD_IMPORT_GATE_2026-09-27.md` for the verified hosted response and remaining data-import gates.
