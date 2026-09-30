# WhAPI transport skill

Use this skill for WhAPI/WhatsApp transport changes.

## Current CRM architecture

- The CRM uses one lead path only.
- The CRM source is `+919148338801`.
- New provider messages arrive by webhook at the Supabase Edge Function `whapi-crm-webhook`.
- The webhook records an append-only activity row in `crm_webhook_events` before lead/message processing.
- Existing source-phone records receive another `crm_messages` row ordered by provider `message_at`.
- A new source-phone record creates a CRM lead directly; there is no intake queue or qualification gate in the data path.
- The UI receives a sanitized Supabase Realtime notification and refreshes its authenticated lead data; it does not poll WhAPI.
- No automatic WhatsApp send is part of the CRM path.

## Transport boundary

The shared WhAPI package only parses and authenticates provider transport. It must not classify traffic into listener categories or decide business ownership.

Inventory automation, where retained for legacy non-CRM workflows, is not connected to the CRM webhook and must not reintroduce listener terminology into the CRM path.

## Safety

- Never expose WhAPI tokens or Supabase secret keys.
- Do not call WhAPI to fetch new messages; the provider webhook is the live ingress.
- Do not send messages automatically from the CRM.
- Do not add a second lead staging/intake layer.
