# EFPS CRM — Render Configuration

> Verified 2026-10-05. Older candidate/deployment statements below are historical and superseded.

## Production service

- Service: srv-darsv560tbcc73cu4ip0
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: crm-ui-dashboard
- Auto-deploy: enabled on commit

## Runtime boundaries

- Webhook ingress is Supabase-first and durable; Render is not the WhatsApp webhook persistence boundary.
- Pending WhatsApp group messages are routed to group_message / Group Message / Unqualified before CRM lead promotion can occur.
- Inventory sync endpoint is signed and invoked by Supabase cron.
- AI scheduler endpoint remains HMAC-protected and separate. The deterministic scheduler endpoint uses a dedicated secret and is invoked hourly by Supabase cron job crm_deterministic_scheduler_1h.
- Automatic WhatsApp sending remains disabled; drafts require operator review and pre-send grounding.
- WhAPI API safety: non-catalog API operations are hard-blocked in the shared client; webhook ingestion remains a separate path.

## Release verification

- Current live deploy: dep-db1b2svf3r2c73brd6m0, commit 1982c7ea0a158ee0edcb00fad43e021876c13b9d, status live.

A candidate is not production-live until Render reports the candidate SHA live and the production health/process audit is rerun. This document must not contain an older SHA as the current live commit.

## External credential hardening

AWS least-privilege rotation requires authorized AWS IAM administration. Do not mark the rotation complete based only on repository configuration.

## AI scheduler — intentionally paused

- `crm_ai_scheduler_6h` is **paused** as of 2026-10-04.
- Its implementation and `crm_invoke_ai_scheduler()` function remain in the repository and database.
- The pg_cron trigger has been removed, so no recurring AI scheduler execution is currently scheduled.
- The deterministic classification scheduler remains active independently at `0 * * * *`.
- Reactivation requires an explicit operational decision and a new scheduler activation.
