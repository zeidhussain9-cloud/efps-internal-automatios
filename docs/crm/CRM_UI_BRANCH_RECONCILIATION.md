# CRM UI branch reconciliation

**Canonical UI branch:** `crm-ui-dashboard`
**Reference branch:** `main` (unchanged by CRM UI work)
**Checkpoint:** 2026-09-30

## Current contract

- GitHub contains only the intended `crm-ui-dashboard` and `main` branches for the UI workstream.
- CRM lead scope is source `+919148338801`.
- Historical production population is 228 leads and 5,286 messages.
- Historical message provenance remains source-backed; SQLite message IDs are stored as `source_message_id`, not fabricated provider IDs.
- The live CRM path is lead-only. There is no listener abstraction, no inventory listener, no lead listener, no intake queue and no qualification gate.
- WhAPI pushes `messages` webhooks to the Supabase Edge Function `whapi-crm-webhook`.
- `crm_webhook_events` records the webhook activity before lead/message processing.
- Existing source-phone leads receive appended messages; unseen source-phone contacts create leads directly.
- `crm_messages` is rendered chronologically by provider `message_at`.
- Supabase Realtime signals the UI after message insertion; the browser does not poll WhAPI or poll the CRM workspace.
- The CRM never sends WhatsApp messages automatically.
- Render remains the authenticated UI/API host. Supabase is the live webhook ingress and CRM database. No AWS runtime is used for the CRM webhook.

## Data gates completed

The historical import has been executed and reconciled: 5,286 messages for the 228-lead source population. No synthetic lead rows are present. No intake contacts are present.

## Live webhook gate

The Supabase Edge Function is deployed and custom-authenticated. A correct-auth empty webhook returned HTTP 200; an invalid token returned HTTP 401. A transactional lead/message processing test was rolled back, leaving the verified counts unchanged at 228 leads and 5,286 messages.

The remaining external cutover action is the WhAPI provider setting itself: the connected WhAPI channel must point its `messages` webhook to the Supabase function URL and send the shared webhook secret header. The current local provider credential lookup did not return a usable active channel during this checkpoint, so no provider setting was guessed or mutated.

## Canonical technical document

See `docs/crm/CRM_LIVE_WHAPI_WEBHOOK.md` for the complete live architecture, event table, lead association rules, ordering, Realtime behavior and security boundary.
