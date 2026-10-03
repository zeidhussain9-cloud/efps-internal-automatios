# EFPS CRM — Housing Inventory Sync Runbook

> **Current verified snapshot: 2026-10-03 18:04 IST (12:34 UTC).**

## Source and boundary

The canonical source is the `Housing_Listings` tab. CRM reads the operational A:AT range only. Reserved AU/AV fields are outside the CRM mirror and are not written by the CRM.

## Runtime

- Render service: `srv-darsv560tbcc73cu4ip0`
- Branch: `crm-ui-dashboard`
- Inventory sync endpoint: protected and HMAC authenticated
- Supabase job: `crm_inventory_sheet_reconcile_5m`
- Cadence: every 5 minutes

## Current evidence

- Active inventory rows: **88**
- Post-release sync runs in the audited window: **372**
- Every audited run: **88 rows / 0 changed / 0 removed**
- Inventory change-ledger rows in the audited window: **0**
- Latest observed sync timestamp: **2026-10-03 12:30:01 UTC**

The snapshot uses source hashes, a transaction and an advisory lock. Empty source snapshots are rejected to prevent mass tombstoning. New inventory differences are recorded in `crm_inventory_sync_changes`.

## Operating rule

Do not treat historical inventory edit history before the change ledger was introduced as reconstructable. New changes are field-level and durable.