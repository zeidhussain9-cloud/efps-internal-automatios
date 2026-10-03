# EFPS CRM — Database Migration / Production Gate

> **Current verified state: 2026-10-04 01:19 IST (19:49 UTC).**

The historical pre-production migration gates are closed for the current CRM deployment. Production schema migrations through the unified AI scheduler are applied. The AI scheduler trigger is intentionally paused as of 2026-10-04; its implementation remains installed but no recurring pg_cron job is active.

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