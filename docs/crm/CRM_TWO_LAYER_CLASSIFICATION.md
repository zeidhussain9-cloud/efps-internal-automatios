## Current production audit — 2026-10-01 (post-reconciliation)

Verified live state: Render `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, branch `crm-ui-dashboard`, deploy `dep-dav55km0tbcc73eelat0`, commit `da13083f6cb1f3c78ec3f4df661c515d43f556fa`. Supabase source `+919148338801`: 186 leads, 307 classifications, 20 pending, 186 promoted, and 6,853 CRM messages. All 436 webhook events are processed; 0 remain `received` or `processing`; 0 failed. Automatic reconciliation is active. Browser Realtime is notification-only and CSP allows the exact Supabase HTTPS/WSS origin. RLS is enabled on all CRM tables and `anon`/`authenticated` have no SELECT privilege.

# CRM Two-Layer Classification and Webhook Gate

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



## Current production behavior — 2026-09-30

The Contact Classification screen is intentionally simple: one queue with two tabs.

- **Not pushed to CRM:** pending and non-qualified contacts.
- **Qualified leads pushed to CRM:** contacts successfully promoted into Lead CRM.

The operator selects one classification and clicks **Update**. A non-qualified choice saves as excluded and remains outside Lead CRM. A **Qualified Lead** choice executes the transactional promotion path and moves the contact only after the database confirms success. Each row includes a direct **Open WhatsApp** link.

The 2026-09-30 production failure was PostgreSQL `42P18` in the new-lead insert. The cause was an untyped `$5` parameter inside `jsonb_build_object()`; the consolidated fix explicitly casts `$5::text`. The operator retry succeeded after deployment.

## Canonical flow

1. WhAPI callback arrives for the connected source `+919148338801`.
2. The Supabase Edge Function authenticates the callback and persists the callback in `crm_webhook_events`.
3. The webhook event is not rejected because the contact is unknown or non-qualified.
4. Message events with a resolvable phone are reconciled into `crm_contact_classifications`.
5. Contact classification is Layer 1: Qualified Lead; Personal / Family; Agent / Partner; Business; Promotion / Marketing; Vendor / Supplier; Internal; Cold Inquiry; Property Listing Sent; Unknown / Pending.
6. Only Qualified Lead is eligible to create/promote a `crm_leads` record.
7. `crm_leads.lead_type` is Layer 2 and describes the operational state of an already-qualified lead.
8. Qualified live messages are appended to `crm_messages` using provider message identity and original message timestamp.
9. Non-qualified contacts remain in the classification/event layers; their events are not promoted into CRM.
10. If a non-qualified contact is later classified as Qualified Lead, the promotion path creates the lead and backfills preserved message events.

## Credential boundary

The WhAPI channel API token is a provider credential. It is not a semantic classifier and is not required by the inbound webhook receiver. The inbound receiver uses a separate webhook authentication secret. Production secret material must not be committed to GitHub or placed in the Render browser/API environment unnecessarily.

## Historical data rule

The historical SQLite archive remains source evidence. It must not be reclassified from aggregate statistics. Current production Supabase records carry their own source and webhook provenance.

## No intake queue

`crm_intake_contacts` / `crm_intake_messages` are not part of this architecture. The classification registry replaces the intake queue.

## Inventory

Inventory sender/source routing is outside this CRM classification path and remains unchanged.
