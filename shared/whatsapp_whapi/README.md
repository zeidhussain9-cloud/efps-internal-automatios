# Shared WhAPI transport

## Authoritative current verified state — 2026-10-05

This is the current repository/runtime boundary. Older dated checkpoints below are historical evidence.

- Deployment branch: crm-ui-dashboard
- Current CRM commit: 1982c7ea0a158ee0edcb00fad43e021876c13b9d
- Render deployment: dep-db1b2svf3r2c73brd6m0 (LIVE)
- Production health: GET /health = HTTP 200
- Production source: +919148338801
- Supabase: 253 leads; 9,224 messages; 3,025 persisted webhook events; 389 classifications; 253 normalized lead requirements; 88 inventory rows.
- Webhook failures: 0 in the current production database checkpoint.
- API safety: EFPS_WHAPI_API_ENABLED=false by default; EFPS_WHAPI_CATALOG_WRITE_ENABLED=false by default; EFPS_WHAPI_WEBHOOK_ENABLED=true by default.
- Non-catalog WhAPI API operations are hard-blocked by the shared client.
- Webhook ingestion is independent of the API safety flags.
- Catalog-repair admin endpoint/workflow has been removed.
- Current repository verification: 134/134 tests, browser 1/1, build PASS.

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

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The current repository verification is 134/134 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.



This package contains only technical WhatsApp/WhAPI transport primitives: authentication, channel/settings access, webhook payload normalization and provider-safe message parsing.

## CRM live path

The CRM does not use source listeners, inventory listeners, lead listeners, polling, or a server-side WhAPI fetch loop. Direct WhAPI API access is disabled by policy; the webhook remains the live ingress boundary. The production CRM path is:

`WhAPI messages webhook -> Supabase Edge Function -> crm_webhook_events -> crm_leads + crm_messages -> Supabase Realtime -> CRM UI`

The connected CRM source is `+919148338801`. Every accepted webhook message is treated as lead activity. Existing leads receive another chronological message; a previously unseen customer phone creates a lead row directly.

The CRM does not send WhatsApp messages automatically, and the shared WhAPI client hard-blocks non-catalog API operations.

## Parser boundary

The shared parser normalizes common text, link-preview, location, image, video, document and audio message shapes. It does not decide whether a message is inventory, a lead, a promotion or any other business object.

Webhook event names and live settings must be verified against the provider's current settings before a live configuration change. This module does not mutate live provider settings automatically.


## Current safety boundary

Verified 2026-10-05: the shared WhAPI client defaults EFPS_WHAPI_API_ENABLED=false, EFPS_WHAPI_CATALOG_WRITE_ENABLED=false, and EFPS_WHAPI_WEBHOOK_ENABLED=true. All non-catalog WhAPI API operations are hard-blocked by the client allowlist. The webhook integration is a separate ingestion boundary and is not disabled by these API safety flags.

The former catalog-repair admin endpoint/workflow was removed. No current production code path may silently re-enable WhAPI API traffic.
