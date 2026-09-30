# CRM UI branch reconciliation

**Canonical UI branch:** `crm-ui-dashboard`
**Reference branch:** `main` (reconciled repository branch; not the Render deployment branch)
**Checkpoint:** 2026-09-30 — commit `184abfe58052b01ebf5be4dd26044f31fc579536`

## Current contract

- GitHub contains only the intended `crm-ui-dashboard` and `main` branches for the UI workstream.
- The UI source selector exposes all three audited EFPS WhatsApp source numbers: `+919148338801`, `+917975102130`, `+919902024973`. The connected live WhAPI ingress remains `+919148338801`.
- Current production evidence is 141 source-linked CRM leads, 287 classifications, 58 pending classifications, and 6,561 CRM messages for `+919148338801`. The 5,286-message historical SQLite archive remains historical source evidence and must not be treated as the complete current CRM message count.
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

The current production CRM registry contains 141 source-linked leads and 287 classifications, with 58 pending classifications. Current CRM messages total 6,561 for the production source. No separate intake queue is used.

## Live webhook gate

The Supabase Edge Function is deployed and custom-authenticated. A correct-auth empty webhook returned HTTP 200; an invalid token returned HTTP 401. A transactional webhook processing test was rolled back. Current persisted counts are 141 source-linked leads, 287 classifications, 6,561 messages and 28 webhook events. Thirteen webhook events are processed and fifteen remain in `received`; this is an operational reconciliation backlog, not evidence that another WhAPI historical extraction occurred.

The WhAPI-to-Supabase live ingress is enabled for the current production source. Do not run another historical WhAPI API extraction as part of ordinary CRM reconciliation. Historical SQLite evidence and live webhook data remain distinct provenance classes.

## Canonical technical document

See `docs/crm/CRM_LIVE_WHAPI_WEBHOOK.md` for the complete live architecture, event table, lead association rules, ordering, Realtime behavior and security boundary.


## Classification write fix — 2026-09-30

A single operator test on contact `+919216063368` produced the definitive Render diagnostic: PostgreSQL `42P18`, `could not determine data type of parameter $5`, at the `insert lead` stage. The failing parameter was the source number passed into `jsonb_build_object()` during new-lead creation. The consolidated fix explicitly casts that parameter to `text`. Local build and the full 62-test suite passed before deployment. Render deployment `dep-daul3fpsrm7s73b27l00` is live from commit `184abfe58052b01ebf5be4dd26044f31fc579536`. The subsequent operator retry succeeded.
