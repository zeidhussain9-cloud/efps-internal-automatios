# EFPS CRM — Render Configuration

> Verified 2026-11-12 14:45 IST against Render service metadata, live deployment, health endpoint and Supabase sync evidence.

## Production service

- Service: `srv-darsv560tbcc73cu4ip0`
- Name: `easyfind-crm-d01-d05`
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: `crm-ui-dashboard`
- Auto-deploy: enabled on commit
- Latest live deployment: `dep-dbqo57o473hc73881mdg`
- Live commit: `97dff533cfeee3138866277430a471ccc8369ac3`

## Runtime boundaries

- Webhook ingress is Supabase-first and durable; Render is not the WhatsApp webhook persistence boundary.
- `whapi-crm-webhook` is ACTIVE v10. Null-phone messages are persisted without fake contacts; group messages are never linked to a promoted lead timeline.
- Inventory sync endpoint is HMAC authenticated and invoked by Supabase cron `crm_inventory_sheet_reconcile_5m` every five minutes.
- The inventory sync inserts the parent `crm_inventory_sync_runs` row before child `crm_inventory_sync_changes` rows to satisfy the foreign key.
- The deterministic scheduler endpoint uses a dedicated secret and is invoked hourly by `crm_deterministic_scheduler_1h`.
- AI scheduler `crm_ai_scheduler_6h` remains intentionally paused.
- Automatic WhatsApp sending remains disabled; drafts require operator review and pre-send grounding.
- WhAPI API safety: non-catalog API operations are hard-blocked in the shared client; webhook ingestion remains a separate path.

## Release verification

- Latest Render deployment `dep-dbqo57o473hc73881mdg` is LIVE from commit `97dff533cfeee3138866277430a471ccc8369ac3`.
- Production `GET /health`: HTTP 200.
- Production `GET /`: HTTP 200.
- Inventory sync: HTTP 200 at 09:11 UTC (104 rows / 104 changed / 0 removed) and 09:15 and 09:20 UTC (each 104 rows / 0 changed / 0 removed).
- Protected inventory API without operator session returns HTTP 401 as expected.

A candidate is not production-live until Render reports the candidate SHA live and the production health/process audit is rerun. The previous 2026-10-05 SHA is historical, not the current live commit.

## External credential hardening

AWS least-privilege rotation requires authorized AWS IAM administration. Do not mark the rotation complete based only on repository configuration.

## AI scheduler — intentionally paused

- `crm_ai_scheduler_6h` is paused.
- Its implementation and `crm_invoke_ai_scheduler()` function remain in the repository and database.
- The pg_cron trigger has been removed; no recurring AI scheduler execution is currently scheduled.
- The deterministic classification scheduler remains active independently at `0 * * * *`.
- Reactivation requires an explicit operational decision and a new scheduler activation.