# EFPS CRM — Database Migration / Production Gate

> **Current verified state: 2026-10-03 18:04 IST (12:34 UTC).**

The historical pre-production migration gates are closed for the current CRM deployment. Production schema migrations through the unified AI scheduler are applied.

## Active production invariants

- CRM application uses server-side Supabase access.
- Webhook and scheduler functions run with controlled privileged execution.
- CRM data tables are not exposed directly to `anon`/browser clients.
- Scheduler calls are HMAC authenticated.
- Inventory sync is HMAC authenticated.
- AI scheduler persistence uses idempotency and checkpoint fields.

## Remaining external infrastructure evidence

Encrypted backup/isolated restore remains an external infrastructure evidence item; it is not a missing schema migration. AWS least-privilege credential rotation is also external IAM work.

Do not reopen historical source-reconciliation or synthetic-import gates unless a fresh audit demonstrates a regression.