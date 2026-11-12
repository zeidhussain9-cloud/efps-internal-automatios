# CRM live WhAPI webhook — current verified state

> Revalidated 2026-11-12 against production Supabase, the active Edge Function, scheduler state and GitHub release evidence.

## Production identity

- Render: easyfind-crm-d01-d05 / srv-darsv560tbcc73cu4ip0
- Live deployment: dep-dbqod1nf3r2c73fe2gc0
- Live commit: d4083c8c33802f33295b090b9b1c4e71453b5090 on crm-ui-dashboard
- Supabase project: qttcutwzehtskfcwxkwj
- Edge Function: whapi-crm-webhook, ACTIVE v10
- Production source: +919148338801

## Canonical event flow

WhAPI message webhook -> Supabase Edge Function (shared-secret validation) -> crm_webhook_events (durable first write + deduplication) -> crm_process_webhook_event -> crm_messages (every message event, including phone-null) -> crm_contact_classifications when a valid personal phone exists -> deterministic qualification scheduler -> crm_leads only for qualified/promoted contacts.

Render is not the WhatsApp persistence boundary. Supabase stores the event payload before downstream processing.

## Reconciliation since 2026-10-05

- Message events: 18,641.
- Linked crm_messages: 18,641 / 18,641.
- Current processing errors: 0.
- Original phone-constraint error instances: 43, all preserved in processing_error_history.
- Phone-null message events: 6,652, stored without fabricated contact identities.
- Raw event payloads remain intact.
- crm_webhook_reconcile_1m remains active.

## Group-message handling

A chat_id ending in @g.us is a group-chat signal.

- Group payloads and message rows remain stored.
- Phone-null group events do not create contact classifications.
- If a sender already has a promoted personal classification, the group message is still not attached to that lead timeline; the personal classification is not demoted.
- Group messages since 2026-10-05: 13,611; current group-event lead links: 0.
- Historical erroneous group-to-lead links were removed with prior lead/chat associations retained in reconciliation_history.

## Deterministic qualification and AI boundary

- Deterministic scheduler crm_deterministic_scheduler_1h is active hourly.
- Since 2026-10-05: 923 completed / 0 failed; cumulative counts across runs: 319 candidates, 118 qualified, 8 unqualified, 193 pending.
- Current CRM leads: 371; auto_qualified=true: 138.
- Deterministic classification does not call AI.
- The recurring AI scheduler remains intentionally paused and is not scheduled.
- No automatic WhatsApp send path is enabled; drafts require operator review and a manual send action.

## Recent inbound interpretation

The recent two-hour sample was dominated by group/newsletter events. It did not provide a fresh one-to-one personal conversation to exercise a new lead promotion. The full event-to-message reconciliation is healthy, but a new personal inbound qualification path was not independently exercised in this sample.

## Verification

- GitHub Actions CRM UI Verification: build PASS, 139/139 automated tests PASS, browser regression 1/1 PASS.
- CRM synthetic CI: PASS.
- Production-health smoke job was skipped.
- An authenticated live CRM browser session was not used in this follow-up.