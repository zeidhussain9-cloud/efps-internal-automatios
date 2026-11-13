# EFPS CRM — Render Configuration

> Revalidated 2026-11-13 against the signed-in production browser, Supabase projection, and prior release health check.

## Production service

- Service: srv-darsv560tbcc73cu4ip0
- Name: easyfind-crm-d01-d05
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: crm-ui-dashboard
- Auto-deploy: enabled on commit
- Verified live deployment: `dep-dbrev7ajnfac739de33g`
- Live commit: `61688164b25f7a7a8e6df8248f91987a9c471ef6`

## Runtime boundaries

- Supabase is the durable WhatsApp webhook ingress and CRM database.
- whapi-crm-webhook is ACTIVE v10; phone-null messages are persisted without fake contacts.
- Group messages are retained as evidence but never attached to a promoted lead's personal timeline.
- Notion page events update the existing Supabase inventory projection. The old `crm_inventory_sheet_reconcile_5m` Sheets job was removed on 2026-11-13.
- Inventory sync inserts the parent crm_inventory_sync_runs row before child crm_inventory_sync_changes rows.
- Deterministic qualification is invoked hourly by crm_deterministic_scheduler_1h.
- AI scheduler remains intentionally paused; automatic WhatsApp sending remains disabled.

## Release verification

- Render was observed live from `61688164b25f7a7a8e6df8248f91987a9c471ef6`; `/health` and `/` returned HTTP 200 in the release check.
- Signed-in production inventory showed 104 Notion-owned properties (87 Available / 17 Rented). A real Notion edit appeared through Supabase in the dashboard.
- A real delete soft-deleted the Supabase projection after about one minute. Restoring from Notion Trash produced no observed Lambda or Supabase Edge Function request; the projection stayed deleted. End-to-end restore is an open blocker.
- Test snapshot and intake rows were removed, and the test page was permanently deleted from Notion Trash after user approval.
- Earlier code-bearing release checks passed Inventory Contract (130/130), SAM build/validation, CRM build/tests/browser and production health smoke. A new Inventory Contract pass for the latest documentation-only commit is not evidenced.

## External credential hardening

AWS least-privilege rotation and independent encrypted backup/isolated-restore proof remain external infrastructure prerequisites until separately evidenced.

## AI scheduler — intentionally paused

The AI scheduler implementation remains available, but no recurring AI cron trigger is installed. Reactivation requires a separate explicit operational decision.