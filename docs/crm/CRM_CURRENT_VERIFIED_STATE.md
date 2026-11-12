# EFPS CRM — Current Verified State

> Verified 2026-11-12 14:50 IST / 09:20 UTC against production Supabase, Render, GitHub, the canonical Housing_Listings sheet, and local build/test evidence. Older dated audit blocks are historical evidence.

## Runtime

- Production URL: https://easyfind-crm-d01-d05.onrender.com
- Render service: easyfind-crm-d01-d05 / `srv-darsv560tbcc73cu4ip0`
- Live deployment: `dep-dbqo57o473hc73881mdg`
- Live commit: `97dff533cfeee3138866277430a471ccc8369ac3`
- Production branch: `crm-ui-dashboard`
- Supabase project: `qttcutwzehtskfcwxkwj`
- Supabase Edge Function: `whapi-crm-webhook`, ACTIVE v10
- Production source: `+919148338801`

## Production data

- CRM leads: **371**; deterministic auto-qualified: **138**; other leads: **233**.
- Contact classifications: **839** total — 371 promoted, 88 classified, 96 pending, 284 excluded.
- CRM messages: **18,970** created since 2026-10-05.
- WhAPI message events since 2026-10-05: **18,621**; all 18,621 link to `crm_messages`; 0 current processing errors.
- Original phone-constraint errors: **43** since 2026-10-05. All are reconciled; original error text is retained in `processing_error_history`, and raw webhook payloads remain unchanged.
- Phone-null message events since 2026-10-05: **6,641**; all are now stored in `crm_messages` with no fabricated contact/classification.
- Group messages since 2026-10-05: **13,592**; **0** are linked to a lead timeline. A historical all-time cleanup unlinked **1,809** group messages across 12 leads / 10 group chats; previous lead IDs and chat IDs are retained in `reconciliation_history`.
- Deterministic scheduler since 2026-10-05: **922 completed / 0 failed**; latest observed run 2026-11-12 09:00 UTC.
- AI scheduler remains intentionally paused; no AI cron trigger is installed.

## Inventory synchronization

- Canonical source: Google Sheet `Housing_Listings`, operational columns A:AT only. Reserved AU/AV remain outside the CRM mirror.
- Canonical Sheet rows: **104**; Supabase snapshot: **104 active rows** — 87 Available / 17 Rented Out.
- `crm_inventory_sheet_reconcile_5m` is active at five-minute cadence.
- Post-fix syncs: 2026-11-12 09:11 UTC — 104 rows / 104 changed / 0 removed; 09:15 UTC and 09:20 UTC — each 104 rows / 0 changed / 0 removed. Both returned HTTP 200.
- Confirmed failure cause: inventory change rows were inserted before their parent `crm_inventory_sync_runs` row, violating the `crm_inventory_sync_changes.run_id` foreign key. The transaction now inserts the parent first; a regression test enforces the order.

## Slack property reconciliation

- Slack intake bot emitted 17 listing confirmations. The canonical Sheet and Supabase contain **16 unique rows** from this batch.
- `EF-2611-NFHV` is not a separate current Sheet row; its Bellandur 2-BHK details are repeated in the later `EF-2611-B42K` row, which adds the explicit `Semi Gated` value and 10 photos. Treat NFHV as a duplicate/replaced intake, not a missing property to insert again.
- The other 16 IDs are present in both the canonical Sheet and `crm_inventory_snapshot`.
- Eight initial Slack confirmations reported Needs Review. Seven surviving rows now have Sheet status Pending, valid `internal_property_type=Semi Gated`, and empty `error_notes`; the eighth (NFHV) is the duplicate/replaced entry. The current Sheet has no active `Needs Review` status rows. The CRM sync did not write or change Sheet statuses.

## Webhook and qualification safeguards

- Webhook ingress remains Supabase-first and durable; reconciliation runs every minute.
- Phone-null messages are stored without creating fake contacts.
- Group-chat messages are retained as evidence but never attached to a promoted lead's personal timeline. Existing contact classifications are not demoted.
- Deterministic qualification remains independent of AI. AI runs/drafts remain operator-triggered; no automatic WhatsApp sends are enabled.

## Verification

- Node: **24.22.3** (within the repository's Node 24 engine range).
- `npm run build`: PASS.
- `npm test`: **139/139 PASS**.
- `npm run test:browser`: **1/1 PASS** using installed Chrome via `CHROME_PATH`.
- Production `GET /health`: HTTP 200; `GET /`: HTTP 200.
- Protected `GET /api/inventory/overview` without an operator session: HTTP 401 as expected. The authenticated production inventory response was not directly browser-tested; its Supabase source rows and local browser regression were verified.
- `npm ci` reported 7 dependency advisories (3 moderate, 4 high). No dependency upgrades or force-fixes were applied.

## Repository reconciliation

- The recovery runtime code was released from `crm-ui-dashboard` commit `97dff533cfeee3138866277430a471ccc8369ac3`, tree `c6297dcbe479f877bb97a5e4c37d93c5d14296da`; this dated checkpoint precedes the documentation-only closeout commit.
- `main` remains at `0aae093b8b4fc524aa731d16cf5603d39b830598` pending the post-release fast-forward.
- The Mac checkout is established at `/Users/zeidzakir/Projects/efps-internal-automatios` with the CRM worktree under `leads_automation/crm-ui-dashboard`. The unrelated pre-existing workspace files were preserved.
- Final branch-tree equality is a release gate and is not claimed until `main` is advanced and rechecked.

## Scheduler policy

| Process | Schedule | State |
|---|---|---|
| `crm_webhook_reconcile_1m` | Every minute | Active |
| `crm_inventory_sheet_reconcile_5m` | Every 5 minutes | Active |
| `crm_deterministic_scheduler_1h` | Every hour | Active |
| `crm_ai_scheduler_6h` | Every 6 hours | **Paused** |

Reactivating the AI scheduler requires a separate explicit operational decision.