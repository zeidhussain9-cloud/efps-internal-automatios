# Current production audit — 2026-10-01

## Authoritative current verified state — 2026-10-01 21:55 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **CRM commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **CRM tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **main:** `b2fbf366021852aedd4bf0ec66484ad421fb5662`
- **main tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** `dep-dav82h3m8hqs7399j4ug` = **LIVE**
- **Live Render commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 186 leads; 6,870 messages; 465 webhook events; 310 classifications; 186 requirements; 196 AI runs; 196 drafts; 186 AI cursors; 88 active inventory rows.
- **Classification status:** 186 promoted; 88 classified; 23 pending; 13 excluded = 310 total.
- **Webhook status:** 465 processed; 0 received; 0 processing; 0 failed.
- **Message reconciliation:** 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 829/829 distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 76/76 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v8.
- **AWS legacy webhook:** no changes in the audited CRM hardening range.
- **24-item CRM audit:** GREEN / VERIFIED.

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



This addendum supersedes older numeric checkpoints in this document for current operational state.

- Audit window: first persisted production event **2026-09-30 15:51:11.11684 UTC** through **2026-10-01 11:58:22.584248 UTC** for source `+919148338801`.
- `crm_webhook_events`: **436** persisted events; **436 processed**, **0 received**, **0 processing**, **0 failed**.
- **288** persisted events contain a normalized personal phone and all **288** link to a `crm_messages` row.
- **28** distinct live customer phones were observed; **28/28** have a classification record; 24 classifications were first seen during this live window and 4 pre-existed.
- No duplicate classification rows per source+phone, no phones mapped to multiple promoted leads, no live phones with duplicate CRM leads, and no promoted message is missing its lead.
- Provider/event integrity checks found **0** duplicate event-fingerprint groups, **0** duplicate provider-event-ID groups, and **0** duplicate source-message-ID groups.
- **131** outgoing phone-null events have WhatsApp group JIDs (`@g.us`) and no personal JIDs; these are correctly outside personal lead reconciliation.
- **13** historical webhook rows retain `crm_webhook_events.lead_id=NULL` even though their preserved `crm_messages.lead_id` is now populated. These are pre-promotion events; the promotion transaction backfills messages but does not backfill the original event row. This is a denormalization gap, not a message/lead routing failure.
- The active Supabase Edge Function is `whapi-crm-webhook`, version **6**.

For the full evidence set, see `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.

## Current production audit — 2026-10-01 (post-reconciliation)

See the authoritative current-state block at the top of this document for the current Render commit/deployment and Supabase counts.

## Current production checkpoint — 2026-10-01

- Source in scope: `+919148338801`.
- Supabase current state: 186 leads, 310 classifications, 23 pending classifications, 186 promoted classifications, 6,870 messages.
- `crm_webhook_events`: 73 rows for the source; 73 processed, 0 received, 0 failed. Automatic reconciliation is active; there is no current received-event backlog.
- The historical 5,286-message SQLite archive remains historical source evidence and is not the current CRM message count.
- Do not initiate another WhAPI historical API extraction as part of ordinary reconciliation. Live discovery of new contacts is through the webhook boundary and `crm_contact_classifications`.
- Browser Supabase Realtime is only a notification/refresh mechanism; server-side webhook ingestion and the CRM database are independent of it.


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

- **186 source-linked CRM leads** currently persisted in production
- **307 current classifications** for `+919148338801`, with 2 pending and 186 promoted.
- 6,870 current CRM messages; the 5,286-message SQLite archive remains historical evidence.
- **0 intake contacts**; the intake tables were removed from the CRM live model
- **73 persisted webhook events** at the 2026-10-01 verified checkpoint (73 processed, 0 received, 0 failed)

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
