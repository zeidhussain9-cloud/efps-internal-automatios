## Current production checkpoint — 2026-09-30

- Source in scope: `+919148338801`.
- Supabase baseline: 141 source-linked leads, 287 classifications, 58 pending classifications, 6,561 messages.
- `crm_webhook_events`: 28 rows for the source; 13 processed and 15 currently `received`. The latter are a live operational backlog and should be investigated before any claim of complete event reconciliation.
- The historical 5,286-message SQLite archive remains historical evidence. It is not a second live database and is not interchangeable with the current 6,561-message Supabase count.
- Do not initiate another WhAPI historical API extraction unless explicitly authorized. Live discovery of new contacts is through the webhook boundary and the `crm_contact_classifications` registry.

# CRM live WhAPI webhook — 2026-09-30

# CRM live WhAPI webhook — 2026-09-30

## Canonical flow

```text
WhAPI messages webhook
        |
        v
Supabase Edge Function: whapi-crm-webhook
        |
        +--> crm_webhook_events (durable activity/audit first)
        |
        v
crm_contact_classifications
   | pending                 | promoted
   v                         v
crm_messages            existing crm_lead
   |                         |
   +------------+------------+
                |
                v
       Supabase Realtime
                |
                v
           CRM UI refresh

Operator selects Qualified Lead in Contact Classification before promotion.
```

There is **no listener abstraction** in this path. There is no inventory listener, lead listener, CRM listener, or staged intake queue. `crm_contact_classifications` is the durable pre-lead registry and the operator qualification gate.

## Lead identity

The CRM source is the connected WhatsApp identity `+919148338801`. A customer is represented by the normalized customer phone stored as `crm_lead_sources.source_contact_id` for that source.

- If the source + customer phone already has a promoted lead, the new provider message is appended to that lead.
- If the source + customer phone has no promoted lead, the contact classification row is created/updated with `pending` status and the message is preserved with `lead_id` null.
- Only an operator selecting **Qualified Lead** calls the promotion path, which creates the `crm_leads` row and `crm_lead_sources` row and backfills preserved messages.
- A contact name supplied by WhAPI is stored when the lead has no existing display name.
- If no name is supplied, the phone remains the truthful fallback. No name is fabricated.

This is a two-layer contact-to-lead flow: the classification registry preserves unknown contacts until an operator promotes one into the Lead CRM.

## Webhook activity table

`crm_webhook_events` is append-oriented ingress/audit state. It stores provider event identity, source, customer phone, direction, type, raw normalized message payload, provider timestamp, receipt timestamp, processing state, failure detail, and the resulting lead/message IDs.

The unique key `(provider, provider_event_id)` makes webhook retries idempotent.

Processing states are `received`, `processing`, `processed`, and `failed`. A processing failure is retained as an event rather than silently disappearing.

## Ordering and history

`crm_messages.message_at` is the provider message timestamp. The workspace query orders messages by `message_at ASC, id ASC`, so imported history and new webhook activity appear in chronological order. The original SQLite message identity remains in `source_message_id`; WhAPI provider IDs use `provider_message_id`.

Current verified source population:

- **141 source-linked CRM leads** currently persisted in production
- **228 historical classifications** for `+919148338801`, currently all non-pending
- **6,561 current CRM messages**; the **5,286-message SQLite archive** remains historical evidence
- **0 intake contacts**; the intake tables were removed from the CRM live model
- **0 persisted live webhook events** at the reconciliation checkpoint

## UI live updates

The browser does not poll WhAPI and does not poll the CRM workspace. A Postgres trigger emits a sanitized Supabase Realtime broadcast after `crm_messages` insertion. The broadcast contains no customer content and only signals that CRM activity changed. The authenticated CRM API then refreshes the current lead/workspace data.

The UI displays the Realtime connection state. The Realtime channel is a notification mechanism, not a second source of CRM data.

## Security boundary

The Edge Function has JWT verification disabled because WhAPI is an external webhook caller. The function performs its own shared-secret verification before parsing or writing the event. The webhook secret is stored in Supabase Vault and retrieved through a restricted `SECURITY DEFINER` function; it is not committed to source control.

The Render application no longer accepts CRM WhatsApp webhook writes. Its old `/api/webhooks/whatsapp` route is removed. Render remains the authenticated CRM UI/API host; Supabase is the live webhook ingress and database.

## No outbound automation

The CRM webhook only records WhatsApp activity. It never calls a WhAPI send endpoint and never generates or sends a customer reply automatically.

## Validation performed

- Supabase Edge Function deployed and active.
- Correct webhook secret + empty message payload returned HTTP 200.
- Incorrect webhook secret returned HTTP 401.
- Database lead/message processing was exercised inside a transaction and rolled back; the diagnostic transaction was rolled back and did not change persisted production data.
- Intake tables are absent from the production schema.
- Render webhook route was removed and its old environment gate remains disabled.
- UI dependency `@supabase/supabase-js` added for Realtime.

## Operator classification UI — 2026-09-30

Webhook ingestion and operator qualification remain separate stages. Incoming contacts are preserved first. The UI exposes one Contact Classification screen with two sub-tabs: Not pushed to CRM and Qualified leads pushed to CRM. Non-qualified classifications remain outside CRM; Qualified Lead is the only promotion path. The explicit Update action waits for the server transaction to succeed before the UI moves the contact between queues.
