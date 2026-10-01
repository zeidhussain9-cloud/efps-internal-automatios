# CRM UI branch reconciliation

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



**Canonical UI branch:** `crm-ui-dashboard`
**Reference branch:** `main` (reconciled repository branch; not the Render deployment branch)
**Checkpoint:** 2026-10-01 — commit `da13083f6cb1f3c78ec3f4df661c515d43f556fa`, tree `f36a5ccb4bae742e83603b09bee59d01595ecf00`
**`main` checkpoint:** `692bdcbbab51752b8eb7d4927921d1cfc4830de7`, tree `f36a5ccb4bae742e83603b09bee59d01595ecf00`

## Current contract

- GitHub contains only the intended `crm-ui-dashboard` and `main` branches for the UI workstream.
- The UI source selector exposes all three audited EFPS WhatsApp source numbers: `+919148338801`, `+917975102130`, `+919902024973`. The connected live WhAPI ingress remains `+919148338801`.
- Current production evidence is 186 leads, 307 classifications, 20 pending classifications, 186 promoted classifications, and 6,853 CRM messages for `+919148338801`. The 5,286-message historical SQLite archive remains historical source evidence and must not be treated as the complete current CRM message count.
- Historical message provenance remains source-backed; SQLite message IDs are stored as `source_message_id`, not fabricated provider IDs.
- The live CRM path is lead-only. There is no listener abstraction, no inventory listener, no lead listener or staged intake queue. `crm_contact_classifications` is the pre-lead registry and operator qualification gate.
- WhAPI pushes `messages` webhooks to the Supabase Edge Function `whapi-crm-webhook`.
- `crm_webhook_events` records the webhook activity before lead/message processing.
- Existing promoted source-phone leads receive appended messages; unseen source-phone contacts remain classifications/messages until an operator selects Qualified Lead.
- `crm_messages` is rendered chronologically by provider `message_at`.
- Supabase Realtime signals the UI after message insertion; the browser does not poll WhAPI or poll the CRM workspace.
- The CRM never sends WhatsApp messages automatically.
- Render remains the authenticated UI/API host. Supabase is the live webhook ingress and CRM database. No AWS runtime is used for the CRM webhook.

## Data gates completed

The current production CRM registry contains 186 leads and 307 classifications, with 20 pending classifications and 186 promoted. Current CRM messages total 6,853 for the production source. No separate intake queue is used.

## Live webhook gate

The Supabase Edge Function is deployed and custom-authenticated. A correct-auth empty webhook returned HTTP 200; an invalid token returned HTTP 401. A transactional webhook processing test was rolled back. Current persisted counts are 186 leads, 307 classifications, 6,853 messages and 436 webhook events (436 processed, 0 received, 0 processing, 0 failed). Automatic reconciliation is active; this is not evidence that another WhAPI historical extraction occurred.

The WhAPI-to-Supabase live ingress is enabled for the current production source. Do not run another historical WhAPI API extraction as part of ordinary CRM reconciliation. Historical SQLite evidence and live webhook data remain distinct provenance classes.

## Canonical technical document

See `docs/crm/CRM_LIVE_WHAPI_WEBHOOK.md` for the complete live architecture, event table, lead association rules, ordering, Realtime behavior and security boundary.


## Classification write fix — 2026-09-30

A single operator test on contact `+919216063368` produced the definitive Render diagnostic: PostgreSQL `42P18`, `could not determine data type of parameter $5`, at the `insert lead` stage. The failing parameter was the source number passed into `jsonb_build_object()` during new-lead creation. The consolidated fix explicitly casts that parameter to `text`. Local build and the full 62-test suite passed before deployment. Render deployment `dep-daum4rtg1s2s73cntsv0` is live from commit `45dbab7b1ba92387e5e001f74929ad40c92be6a9`. The subsequent operator retry succeeded.
