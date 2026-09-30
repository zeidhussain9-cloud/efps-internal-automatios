# CRM UI branch reconciliation

**Canonical UI development branch:** `crm-ui-consolidated`  
**Protected reference branch:** `main` (not used for ongoing UI changes)  
**Reconciliation checkpoint:** 2026-09-30

## Scope

This branch is the single working line for the EFPS CRM UI dashboard and its production lead-workspace data path.

The branch starts from the verified current `main` production snapshot so that the already-merged UI, inventory, Render hardening, and production-data cleanup are retained without rewriting `main`.

## Branch reconciliation

The GitHub branch comparison at this checkpoint showed:

| Branch | Relationship to current main | Disposition |
|---|---|---|
| `crm-production-test-hardening` | Diverged; its test changes are already represented in the merged production snapshot | Historical branch retained; no duplicate merge |
| `crm-production-228-only` | Diverged; production 228-only UI/data-scope changes are already represented in current main | Historical branch retained; no duplicate merge |
| `crm-live-lead-workspace` | Diverged; live workspace repository/server/UI/AI changes are already represented in current main | Historical branch retained; no duplicate merge |
| `crm-ui-dashboard` | Behind current main | Superseded by current production snapshot |
| `crm-inventory-source-sync-20260927` | Behind current main | Inventory work already represented in current main |
| `inventory-supabase-sync-20260927` | Historical source-sync branch | Not a separate UI line |
| `crm/source-of-truth-reconciliation` | Historical reconciliation branch | Not a separate UI line |
| `audit/housing-inventory-source-of-truth-2026-09-26` | Historical audit branch with broad non-UI material | Kept as audit evidence, not a UI development line |

No force-push or rewrite of `main` is performed by this consolidation.

## Current production UI contract

- Lead list is restricted to source `+919148338801`.
- The current historical population is 228 leads.
- Lead workspace has explicit back navigation to Leads Inbox.
- Classification is a first-class lead attribute and is sourced from the historical extraction.
- Historical conversation messages use source-backed SQLite message identity; no provider ID is fabricated.
- The browser polls an open lead workspace so newly ingested messages appear without a manual reload.
- A gated server webhook accepts normalized live WhatsApp events for the configured source when database writes and ingestion are explicitly enabled.
- No automatic WhatsApp sending is implemented.

## Historical conversation import

The audited source contains 5,286 conversations for the 228 leads in this source. The new read-only preparation script exports those conversations from the original SQLite without modifying the source. The separate import script is idempotent and requires explicit operator approval plus an encrypted target backup.

The conversation import is **prepared but not executed in this checkpoint** because the authorized Mac extraction device is currently offline. The UI therefore does not fabricate historical messages.

## Next operational gate

Bring the authorized Mac/Desktop Commander device online, generate the private 5,286-message conversation export, run the explicit conversation import, reconcile the exact count and sample records, then enable the live webhook only after its provider payload mapping and secret are configured.

