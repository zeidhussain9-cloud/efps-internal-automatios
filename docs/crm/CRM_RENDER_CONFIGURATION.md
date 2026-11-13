# EFPS CRM — Render Configuration

> Revalidated 2026-11-13 against Render service metadata; current Notion projection was verified directly in Supabase.

## Production service

- Service: srv-darsv560tbcc73cu4ip0
- Name: easyfind-crm-d01-d05
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: crm-ui-dashboard
- Auto-deploy: enabled on commit
- Latest live deployment: `dep-dbrbc8gjo6nc73etsmr0`
- Live commit: `6b206ddf07515cff2df82140d86ee873e4ea2965`

## Runtime boundaries

- Supabase is the durable WhatsApp webhook ingress and CRM database.
- whapi-crm-webhook is ACTIVE v10; phone-null messages are persisted without fake contacts.
- Group messages are retained as evidence but never attached to a promoted lead's personal timeline.
- Notion page events update the existing Supabase inventory projection. The old `crm_inventory_sheet_reconcile_5m` Sheets job was removed on 2026-11-13.
- Inventory sync inserts the parent crm_inventory_sync_runs row before child crm_inventory_sync_changes rows.
- Deterministic qualification is invoked hourly by crm_deterministic_scheduler_1h.
- AI scheduler remains intentionally paused; automatic WhatsApp sending remains disabled.

## Release verification

- Render reports deployment `dep-dbrbc8gjo6nc73etsmr0` LIVE from commit `6b206ddf07515cff2df82140d86ee873e4ea2965`; `/health` and `/` both returned HTTP 200.
- Inventory projection: 104 active Notion rows (87 Available / 17 Rented); no Sheet-owned rows or test listings.
- Supabase webhook reconciliation: 18,641/18,641 message events linked, 0 active errors.
- GitHub Actions CRM UI Verification and CRM synthetic CI passed; 139/139 automated tests and browser 1/1 passed.
- Render returned no error logs since the deployment. An authenticated production inventory browser session was not exercised in this follow-up. GitHub Inventory Contract failed on that commit, but the reserved-field audit now passes locally after the Lambda-source fix.

## External credential hardening

AWS least-privilege rotation and independent encrypted backup/isolated-restore proof remain external infrastructure prerequisites until separately evidenced.

## AI scheduler — intentionally paused

The AI scheduler implementation remains available, but no recurring AI cron trigger is installed. Reactivation requires a separate explicit operational decision.