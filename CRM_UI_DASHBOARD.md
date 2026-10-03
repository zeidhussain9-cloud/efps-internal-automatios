# EFPS CRM UI Dashboard — Current State

> Verified 2026-10-03 20:26 IST. Older dated statements in this document are historical evidence and are superseded by this block.

## Production identity

- Render service: srv-darsv560tbcc73cu4ip0
- Production URL: https://easyfind-crm-d01-d05.onrender.com
- Deployment branch: crm-ui-dashboard
- Supabase project: qttcutwzehtskfcwxkwj
- Production WhatsApp source: +919148338801

## Operational status

The dashboard uses the production Supabase CRM data path. Webhook events are durably recorded before reconciliation. Inventory is a read-only CRM mirror of the canonical Housing_Listings source. AI analysis is persisted and operator-controlled; WhatsApp sending is manual.

## Current hardening

- Lead status and contact classification are separate persisted concepts.
- Overdue follow-up attention is based only on persisted open follow-ups.
- Inventory uses full-inventory KPI summaries, filtering, sorting and stale-response protection.
- Webhook reconciliation is automatic and idempotent.
- Pending WhatsApp group-chat traffic is deterministically classified as Group Message and kept in Unqualified leads.
- Scheduled AI uses per-lead evaluation checkpoints and persisted idempotency keys.
- OOC automation uses only the controlled geographic vocabulary; ambiguous/selective/unknown locations remain review-required.
- D08 current UI and operator-control handoff is documented.

## Current database snapshot

228 leads; 7,746 messages; 1,471 webhook events; 277 AI runs; 214 drafts; 354 classifications; 88 active inventory listings.
Classification status for +919148338801: 228 promoted / 88 classified / 27 excluded / 11 pending.

## Group Message classification

Pending contacts whose persisted webhook payload has a chat_id ending in @g.us are deterministically classified as Group Message. The classification code is group_message, the label is Group Message, the status is excluded (Unqualified), and the rule source is webhook_rule. Group chat ID/name and rule provenance are retained in evidence. Existing promoted leads are never demoted and operator-classified records remain under operator control.

The same rule is implemented in the Supabase webhook Edge Function and canonical SQL webhook reconciliation function. The current production backfill found 14 pending contacts with persisted group-chat events; all 14 are now group_message / excluded.

## Release note

This document is a point-in-time production statement. Do not copy its values into future documentation without re-verifying the live database and Render deployment.