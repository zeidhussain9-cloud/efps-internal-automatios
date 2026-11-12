# CRM live WhAPI webhook — current verified state

> Verified 2026-11-12 14:50 IST / 09:20 UTC. Earlier dated audit sections are retained in the separate audit documents and are not current-state declarations.

## Production identity

- Render service: `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- Live Render deployment: `dep-dbqo57o473hc73881mdg`
- Live CRM commit: `97dff533cfeee3138866277430a471ccc8369ac3`
- Production branch: `crm-ui-dashboard`
- Supabase project: `qttcutwzehtskfcwxkwj`
- Edge Function: `whapi-crm-webhook`, ACTIVE v10
- Production source: `+919148338801`

## Canonical event flow

```text
WhAPI message webhook
  -> Supabase Edge Function (shared-secret validation)
  -> crm_webhook_events (durable first write + deduplication)
  -> crm_process_webhook_event(...)
  -> crm_messages (every message event, including phone-null)
  -> crm_contact_classifications when a valid personal phone exists
  -> deterministic qualification scheduler
  -> crm_leads only for qualified/promoted contacts
```

Render is not the WhatsApp webhook persistence boundary. Supabase stores the raw normalized event payload before downstream processing. The event's provider ID/fingerprint remains the idempotency boundary.

## Verified reconciliation since 2026-10-05

- `crm_webhook_events` message events: **18,621**.
- Linked `crm_messages`: **18,621 / 18,621**.
- Current processing errors: **0**.
- Historical phone-constraint errors: **43**. All 43 are reconciled; each original error is retained in `processing_error_history`.
- Original `payload` JSON remains unchanged.
- Phone-null message events: **6,641**. All are stored in `crm_messages` without creating a contact classification or fabricated phone.
- The one-minute `crm_webhook_reconcile_1m` cron is active. The reconciler handles received/processing events and bounded batches of previously processed message events that lacked a `crm_messages` link.

## Group-message handling

A persisted `chat_id` ending in `@g.us` is a group-chat signal.

- Group message payloads are retained in `crm_webhook_events` and `crm_messages`.
- A phone-null group event gets no contact classification and no lead link.
- If a valid sender phone exists, the group rule can classify a pending contact as `group_message` / excluded.
- If the sender already has a promoted lead, the group message is still not attached to that lead's personal conversation timeline; the existing contact classification is not demoted.
- Group messages never create or qualify a CRM lead.
- Historical cleanup unlinked **1,809** group messages previously attached to lead timelines, across 12 leads and 10 group chats. Message rows and classifications remain intact. The prior lead ID and group chat ID are preserved per event in `reconciliation_history`; a batch audit activity row records counts.

Current group-message audit since 2026-10-05: **13,592** messages, **0** lead-linked group messages.

## Original 41-event issue — expanded and resolved

The prior audit found 41 affected events. Two additional failures arrived before the fix was deployed, so the final reconciliation covered **43** original errors since 2026-10-05:

- 39 original records were group-chat messages and 2 were newsletter/unsupported chat events at the first audit checkpoint; later arrivals increased the final count.
- The failure was caused by attempting to create `crm_contact_classifications` with a null phone, violating its `NOT NULL` constraint.
- The processor now stores a message without creating a contact when the phone is null.
- The original exception text is appended to `processing_error_history` before the active error field is cleared.
- All 43 events now have a message link, zero current errors, and preserved raw payloads.

## Deterministic qualification and AI boundary

- Deterministic classification is separate from AI and runs hourly.
- Since 2026-10-05: 922 scheduler runs completed, 0 failed.
- Current CRM leads: 371; `auto_qualified=true`: 138.
- AI scheduler `crm_ai_scheduler_6h` remains intentionally paused; no recurring AI scheduler cron is installed.
- AI analysis remains explicitly invoked and persisted; it is not part of webhook qualification.
- No automatic WhatsApp send path is enabled. Drafts require operator review and a manual send action.

## Production checks

- `GET /health`: HTTP 200.
- `GET /`: HTTP 200.
- Protected inventory API without an operator session: HTTP 401 as expected.
- Full local verification: build PASS, 139/139 automated tests PASS, browser regression 1/1 PASS.
- Historical event-count blocks in the 2026-09-30 and 2026-10-01 audit records remain historical evidence only.