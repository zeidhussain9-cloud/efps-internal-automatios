# EFPS CRM — Handoff

> Current verified snapshot: 2026-10-03 20:26 IST. Older dated snapshots below are historical and superseded.

## Production

- Render: srv-darsv560tbcc73cu4ip0
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: crm-ui-dashboard
- Source number: +919148338801
- Supabase: qttcutwzehtskfcwxkwj

## Current data

228 leads; 7,746 messages; 1,471 webhook events; 277 AI runs; 214 drafts; 354 classifications; 88 active inventory listings.
Classification status: 228 promoted, 88 classified, 27 excluded, 11 pending.

## Runtime state

Webhook reconciliation is live through the Supabase Edge Function. A WhatsApp chat_id ending in @g.us is a deterministic Group Message signal for pending contacts. Group Message records remain excluded from CRM leads, while promoted leads are preserved. Automatic WhatsApp sending remains disabled; AI output is operator-reviewed and outbound sending is manual.

## Hardening state

Deterministic OOC assignment and D08 documentation are closed. Group Message classification is implemented, schema-gated, audited, backfilled for current pending group contacts, and deployed to the webhook Edge Function. Independent encrypted backup/isolated restore and AWS least-privilege credential rotation remain external infrastructure prerequisites.

## Release procedure

After runtime verification of this release:
1. Confirm Render reports `e375c1f811e962e140caba2c964fb05cd94ab02a` live.
2. Re-run production webhook/inventory/AI integrity queries.
3. Confirm GitHub CI and browser verification pass.
4. Reconcile the verified tree into `main`.
5. Verify both branch trees are identical.
