# EFPS CRM — Handoff

> **Current verified snapshot: 2026-10-03 18:04 IST (12:34 UTC).**

## Production

- Render: `srv-darsv560tbcc73cu4ip0`
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: `crm-ui-dashboard`
- Release commit: `e375c1f811e962e140caba2c964fb05cd94ab02a`
- Source number: `+919148338801`
- Supabase: `qttcutwzehtskfcwxkwj`

## Current data

186 leads, 7,573 CRM messages, 1,256 persisted webhook events, 214 AI runs, 214 drafts and 88 active inventory listings were observed in the production database during the current audit.

## Runtime state

Webhook reconciliation, inventory reconciliation and the six-hour AI scheduler are active. The current audit found no webhook failures, no pending webhook events, no inventory sync failures, and no scheduled AI failures. Scheduled AI executions persisted checkpoints, idempotency keys and drafts.

## Hardening state

Deterministic OOC assignment and D08 documentation are closed in the application/repository. Independent encrypted backup/isolated restore and AWS least-privilege credential rotation remain external infrastructure prerequisites because the necessary durable backup target, restore target and AWS IAM authorization are not available through the connected interfaces.

Automatic WhatsApp sending remains disabled. AI output is operator-reviewed and outbound sending is manual.

## Release procedure

After runtime verification of this release:
1. Confirm Render reports `e375c1f811e962e140caba2c964fb05cd94ab02a` live.
2. Re-run production webhook/inventory/AI integrity queries.
3. Confirm GitHub CI and browser verification pass.
4. Reconcile the verified tree into `main`.
5. Verify both branch trees are identical.
