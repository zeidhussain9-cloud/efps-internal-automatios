# EFPS CRM — Render Configuration

> Revalidated 2026-11-12 against Render service metadata, live deployment and Supabase sync evidence.

## Production service

- Service: srv-darsv560tbcc73cu4ip0
- Name: easyfind-crm-d01-d05
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: crm-ui-dashboard
- Auto-deploy: enabled on commit
- Latest live deployment: dep-dbqod1nf3r2c73fe2gc0
- Live commit: d4083c8c33802f33295b090b9b1c4e71453b5090

## Runtime boundaries

- Supabase is the durable WhatsApp webhook ingress and CRM database.
- whapi-crm-webhook is ACTIVE v10; phone-null messages are persisted without fake contacts.
- Group messages are retained as evidence but never attached to a promoted lead's personal timeline.
- Inventory sync is HMAC protected and invoked by crm_inventory_sheet_reconcile_5m every five minutes.
- Inventory sync inserts the parent crm_inventory_sync_runs row before child crm_inventory_sync_changes rows.
- Deterministic qualification is invoked hourly by crm_deterministic_scheduler_1h.
- AI scheduler remains intentionally paused; automatic WhatsApp sending remains disabled.

## Release verification

- Render reports deployment dep-dbqod1nf3r2c73fe2gc0 LIVE from commit d4083c8c33802f33295b090b9b1c4e71453b5090.
- Inventory: 104 active rows; latest successful sync 09:55 UTC, 104 rows / 0 changed / 0 removed.
- Supabase webhook reconciliation: 18,641/18,641 message events linked, 0 active errors.
- GitHub Actions CRM UI Verification and CRM synthetic CI passed; 139/139 automated tests and browser 1/1 passed.
- Production-health smoke job was skipped. An authenticated production inventory browser session was not exercised in this follow-up.

## External credential hardening

AWS least-privilege rotation and independent encrypted backup/isolated-restore proof remain external infrastructure prerequisites until separately evidenced.

## AI scheduler — intentionally paused

The AI scheduler implementation remains available, but no recurring AI cron trigger is installed. Reactivation requires a separate explicit operational decision.