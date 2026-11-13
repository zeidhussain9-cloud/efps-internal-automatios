# EFPS CRM — Render Configuration

> Revalidated 2026-11-13 against the signed-in production browser, live Supabase projection, AWS Lambda stack, and current Render deployment.

## Production service

- Service: srv-darsv560tbcc73cu4ip0
- Name: CRM Dashboard (`easyfind-crm-d01-d05`)
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: crm-ui-dashboard
- Auto-deploy: enabled on commit
- Render auto-deploy is enabled on `crm-ui-dashboard`; the current deployed commit and deployment ID are verified directly in Render after each release, rather than duplicated as potentially stale identifiers here.
- The latest signed-in inventory page and `/health` endpoint were rechecked after the current release; see Render for the live deployment record.

## Runtime boundaries

- Supabase is the durable WhatsApp webhook ingress and CRM database.
- whapi-crm-webhook is ACTIVE v10; phone-null messages are persisted without fake contacts.
- Group messages are retained as evidence but never attached to a promoted lead's personal timeline.
- Notion page events update the existing Supabase inventory projection. A 15-minute EventBridge reconciliation is the recovery backstop for missed create/edit/delete/restore events. The old `crm_inventory_sheet_reconcile_5m` Sheets job was removed on 2026-11-13.
- Inventory sync inserts the parent crm_inventory_sync_runs row before child crm_inventory_sync_changes rows.
- Deterministic qualification is invoked hourly by crm_deterministic_scheduler_1h.
- AI scheduler remains intentionally paused; automatic WhatsApp sending remains disabled.

## Release verification

- The signed-in production inventory page shows 104 Notion-owned properties (87 Available / 17 Rented Out). Full source/projection reconciliation reports 0 missing, orphaned, duplicate or semantic field mismatches; all 104 intake events have matching Listing IDs.
- Signed-in production inventory showed 104 Notion-owned properties (87 Available / 17 Rented). A real Notion edit appeared through Supabase in the dashboard.
- Actual Notion `page.undeleted` webhook delivery remains unobserved. The 15-minute EventBridge reconciler now recovers a page that is active in Notion but soft-deleted in Supabase; this fallback was live-tested on rented listing `EF-2609-09B5`.
- Reserved `source_group` and `inventory_locked` are blank across all 104 pages; 43 prior `inventory_locked` values were cleared. Five Rented Out listings have no image URLs in Notion; the CRM correctly shows 99/104 with photos.
- Current recovery release checks passed: `npm run build`; `npm test` (143/143); `npm run test:browser` (1/1); Notion intake pytest (26/26); Edge Function contract tests (4/4); SAM build/lint; Python compileall; repository audit; `git diff --check`.

## External credential hardening

AWS least-privilege rotation and independent encrypted backup/isolated-restore proof remain external infrastructure prerequisites until separately evidenced.

## AI scheduler — intentionally paused

The AI scheduler implementation remains available, but no recurring AI cron trigger is installed. Reactivation requires a separate explicit operational decision.