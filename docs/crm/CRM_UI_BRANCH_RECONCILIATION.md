# CRM UI branch reconciliation

**Canonical UI branch:** `crm-ui-dashboard`
**Reference branch:** `main` (unchanged by CRM UI work)
**Checkpoint:** 2026-09-30

## Current contract

- GitHub contains only the intended `crm-ui-dashboard` and `main` branches for the UI workstream.
- The UI source selector exposes all three audited EFPS WhatsApp source numbers: `+919148338801`, `+917975102130`, `+919902024973`. The connected live WhAPI ingress remains `+919148338801`.
- Current production evidence is 140 CRM leads, 228 historical classifications for `+919148338801`, and 5,286 historical messages.
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

The historical import evidence is reconciled at 5,286 messages and 228 source classifications; the current production CRM registry contains 140 leads. No intake contacts are present.

## Live webhook gate

The Supabase Edge Function is deployed and custom-authenticated. A correct-auth empty webhook returned HTTP 200; an invalid token returned HTTP 401. A transactional webhook processing test was rolled back. Current persisted counts after the UI/data-model reconciliation are 140 leads, 228 classifications, 5,286 messages and 0 live webhook events.

The remaining external cutover action is the WhAPI provider setting itself: the connected WhAPI channel must point its `messages` webhook to the Supabase function URL and send the shared webhook secret header. The current local provider credential lookup did not return a usable active channel during this checkpoint, so no provider setting was guessed or mutated.

## Canonical technical document

See `docs/crm/CRM_LIVE_WHAPI_WEBHOOK.md` for the complete live architecture, event table, lead association rules, ordering, Realtime behavior and security boundary.
