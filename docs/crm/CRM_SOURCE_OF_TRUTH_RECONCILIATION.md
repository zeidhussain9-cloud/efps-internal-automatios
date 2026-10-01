## Current production audit — 2026-10-01 (post-reconciliation)

Verified live state: Render `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, branch `crm-ui-dashboard`, deploy `dep-dav55km0tbcc73eelat0`, commit `da13083f6cb1f3c78ec3f4df661c515d43f556fa`. Supabase source `+919148338801`: 186 leads, 307 classifications, 20 pending, 186 promoted, and 6,853 CRM messages. All 436 webhook events are processed; 0 remain `received` or `processing`; 0 failed. The 33-event operational backlog has therefore been reconciled. Browser Realtime is notification-only and CSP allows the exact Supabase HTTPS/WSS origin. RLS is enabled on all CRM tables and `anon`/`authenticated` have no SELECT privilege. Render reports Basic Auth configured and database connectivity connected.

## Current production truth — 2026-09-30

This document contains historical source-of-truth decisions below. The current operational CRM truth is now split by provenance: the audited local SQLite extraction remains the historical evidence set, while Supabase is the production operational store for the connected source `+919148338801`. Live WhAPI messages enter through the Supabase webhook boundary and are persisted in `crm_webhook_events` before downstream reconciliation.

Current production baseline: 186 leads, 307 classifications, 20 pending classifications, 186 promoted, 6,853 messages, and 436 webhook events (436 processed, 0 received, 0 processing, 0 failed). The current Contact Classification UI is operator-gated; Qualified Lead is the only path into CRM. The two other source numbers remain visible for future onboarding only.

The older statements in this document that WhAPI was a future integration are historical and are superseded by this section.

# EasyFind CRM — Source-of-Truth Reconciliation

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



# EasyFind CRM — Source-of-Truth Reconciliation

**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Canonical UI branch:** `crm-ui-dashboard`  
**Date:** 2026-09-26  
**Scope:** Private local-first EasyFind CRM UI dashboard

## 1. Lead source of truth — explicit owner decision

For this CRM workstream, **the lead source of truth is the local dataset described by `docs/audits/LEADS_EXTRACTION_SOURCE-OF-TRUTH_AUDIT.md`**.

The owner's clarification resolves the previous ambiguity:

- The three WhatsApp backups were manually extracted.
- The extracted data was brought into the local EasyFind lead environment.
- The resulting local SQLite dataset is the lead dataset we will work from.
- The historical Leads Tracker Google Sheet is **not** the CRM lead source going forward.
- The separate live DynamoDB/Slack lead workflow is **out of scope** for this CRM.
- Historical note from the 2026-09-26 checkpoint: the future WhatsApp/WhAPI webhook was then treated as a later integration. That statement is superseded; live WhAPI ingress is now active for `+919148338801`.

The audit document remains the dated evidence record. The CRM implementation must follow its extraction/local-dataset model rather than the excluded live lead workflows.

## 2. Local lead data boundary

### Historical source evidence

Three EFPS WhatsApp source numbers were extracted:

- `+919148338801`
- `+917975102130`
- `+919902024973`

The extraction audit records the 2026-07-23 through 2026-09-23 historical window and the local extraction artifacts.

### Local normalized lead dataset

The local SQLite database identified by the audit contains:

- `leads`
- `conversations`
- `lead_lifecycle_events`

The audit records 735 leads and 23,454 conversation rows in the local database. The audit also documents 6,064 raw extracted messages and explains that filtering/import behavior affects the local normalized result.

For CRM purposes, the **local database is the operational lead dataset**. Its internal historical discrepancies remain documented as data-quality concerns to be handled during local migration/normalization, not by switching the CRM back to the excluded cloud lead systems.

## 3. What is not part of the CRM source of truth

The following are explicitly excluded from the lead source path for this UI work:

- Leads Tracker Google Sheet as an operational lead database
- Slack lead cards/reporting workflow
- DynamoDB lead tables
- Live WhatsApp/WhAPI webhook ingestion

These may exist elsewhere in EasyFind, but they are not used as lead truth by this CRM branch.

## 4. Inventory source for D05

Inventory is a separate business domain.

For D05 UI design, property facts are based on the verified `Housing_Listings` audit and the canonical 48-field inventory contract in the master repository. The inventory pipeline itself remains external to the CRM UI until a later local snapshot/integration phase.

The CRM never invents inventory facts. Availability, rent, furnishing, tenant eligibility, pet state, parking, media state and other property facts must come from the verified inventory dataset when live integration is eventually enabled.

## 5. Local-first CRM model

The future local CRM database is the application layer for the UI and will preserve:

### Source-backed
- customer identity and source relationships
- extracted WhatsApp messages
- message timestamps/direction/type/media references
- source extraction provenance
- local inventory snapshot/reference data when introduced

### Controlled CRM state
- lead status
- priority
- current requirements
- notes
- follow-up state
- property interaction state

### Derived state
- customer intelligence
- requirement proposals
- AI runs
- reply drafts
- deterministic property matches and explanations

### Audit/sync state
- manual edits
- AI attempts
- draft lifecycle
- property actions
- local import/migration checks
- future sync/webhook events

No cloud lead system becomes an alternate CRM source of truth.

## 6. Repository and branch rule

This branch is the single working home for the UI dashboard.

- Base: current `main`
- Branch: `crm-ui-dashboard`
- No CRM changes are made directly on `main`.
- The previous CRM reconciliation branch is historical work only and should not be used for future UI work.
- The old `easyfind-website` CRM branch is historical planning/evidence only.

## 7. Current blockers

Before connecting real local data to the UI:

- normalize/reconcile the local message IDs and any duplicate conversation rows in the extracted dataset;
- verify the actual local SQLite file/schema against the audit;
- build the local CRM schema/migration without changing the source dataset;
- keep all prototype screens synthetic until the local data migration is validated.

These are local data-migration tasks, not reasons to reintroduce the excluded cloud lead systems.
