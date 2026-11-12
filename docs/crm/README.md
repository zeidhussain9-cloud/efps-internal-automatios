# EasyFind CRM Documentation

## Authoritative current verified state — 2026-11-12

Older dated checkpoints below are historical evidence and are not current-state declarations.

- Production: Render `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, LIVE deployment `dep-dbqo57o473hc73881mdg`, commit `97dff533cfeee3138866277430a471ccc8369ac3` on `crm-ui-dashboard`.
- Supabase: `qttcutwzehtskfcwxkwj`; `whapi-crm-webhook` ACTIVE v10.
- CRM: 371 leads; 839 classifications; 18,970 messages since 2026-10-05.
- Webhooks since 2026-10-05: 18,621 message events, all linked to `crm_messages`, 0 current errors; 43 original errors retained in `processing_error_history`.
- Group messages remain evidence but never attach to a lead timeline; 1,809 historical group-message lead links were removed with prior associations retained in `reconciliation_history`.
- Inventory: 104 active rows (87 Available / 17 Rented Out); five-minute Sheet sync is active and returned consecutive HTTP 200 responses after the fix.
- Deterministic scheduler: 922 completed runs / 0 failed since 2026-10-05. AI scheduler intentionally paused; no automatic WhatsApp sends.
- Verification: build PASS; 139/139 automated tests PASS; browser 1/1 PASS.

See `CRM_CURRENT_VERIFIED_STATE.md` for the full current evidence and `CRM_RECOVERY_AUDIT_2026-11-12.md` for the dated recovery record.

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


## 2026-10-01 — Historical production closure status

The CRM browser regression is fixed and D07 is resolved on `crm-ui-dashboard`. D07 covers operator session security, sensitive-data masking, reversible archive, audit visibility, explicit export controls, retention/deletion boundaries and offline handling. D08 remains open.

## 2026-10-01 production AI checkpoint

The CRM AI workspace is now production-enabled on Render service `srv-darsv560tbcc73cu4ip0`. It analyzes the complete stored conversation and lead context rather than fictional fixtures. Requirements are normalized and editable in the Lead Workspace. AI proposals include evidence-backed requirement changes, timeline/context analysis, a suggested lead status, and a versioned reply draft. The AI does not automatically send WhatsApp messages.

## AI scheduler — intentionally paused

- `crm_ai_scheduler_6h` is **paused** as of 2026-10-04.
- Its implementation and `crm_invoke_ai_scheduler()` function remain in the repository and database.
- The pg_cron trigger has been removed, so no recurring AI scheduler execution is currently scheduled.
- The deterministic classification scheduler remains active independently at `0 * * * *`.
- Reactivation requires an explicit operational decision and a new scheduler activation.

## Deterministic classification engine — current verified

- Deterministic classification is active for source +919148338801; it does not call AI.
- New WhatsApp messages remain attached to the same crm_contact_classifications record while a contact is pending; conversation history accumulates in crm_messages and webhook evidence remains in crm_webhook_events.
- The scheduler runs hourly at 0 * * * * through Supabase Cron job crm_deterministic_scheduler_1h.
- Qualification requires customer-originated intent plus property/requirement evidence. Outbound property messages alone cannot qualify a contact.
- Known operator-confirmed Internal, Personal/Family, Agent/Partner, Vendor/Supplier and Group Message exclusions remain protected.
- New automatic decisions are Qualified Lead or an approved Unqualified classification. Property Listing Sent is legacy/historical only and is never generated by the deterministic engine.
- Insufficient evidence remains Waiting for Classification and is reevaluated when new conversation evidence arrives.
- Deterministically qualified leads persist auto_qualified=true and display AUTO QUALIFIED on the lead card.
- Every deterministic evaluation records rule version, evidence message/event IDs, reason and audit provenance.

## Scheduler Reconcile Audit — current contract

Points **40 Requirement field correctness**, **41 Property-matching inputs**, and **42 Property-matching results** are governed by the single canonical contract in `crm-source-audit-scheduler/AUDIT_CONTRACT.md` and the shared implementation in `src/crm-requirement-match-audit.mjs`. The scheduled runner fails closed unless the combined requirement/matching audit is complete. Do not duplicate or redefine these rules in this document.

Historical live population snapshot verified 2026-10-05: **253 promoted qualified leads**, **253 normalized requirement profiles**, **0 missing profiles**, and **71 active canonical inventory listings**. Requirement evidence remains a separate provenance layer and is not fabricated by this audit.