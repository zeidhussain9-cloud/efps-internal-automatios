# EFPS CRM — Production Recovery Audit

**Audit date:** 2026-11-12  
**Window:** 2026-10-05 through 2026-11-12  
**Production source:** `+919148338801`

## Executive result

Inventory synchronization and webhook reconciliation have been repaired and verified in production. The deterministic qualification scheduler remains healthy and unchanged. The AI scheduler remains paused. No automatic WhatsApp sending was enabled.

## 1. Inventory synchronization recovery

### Root cause

The inventory sync transaction inserted rows into `crm_inventory_sync_changes` before inserting the parent `crm_inventory_sync_runs` row. The child table's `run_id` foreign key rejected the change-history insert, causing the transaction to roll back and the HMAC-protected endpoint to return HTTP 502.

### Fix and production evidence

- Parent sync-run row is now inserted before child change-history rows in the same transaction.
- Regression test asserts the parent-before-child SQL order.
- Live Render deployment `dep-dbqo57o473hc73881mdg` is running commit `97dff533cfeee3138866277430a471ccc8369ac3`.
- First catch-up sync: 2026-11-12 09:11:54 UTC, HTTP 200, 104 rows, 104 changed, 0 removed.
- Next scheduled five-minute syncs: 09:15:01 and 09:20:01 UTC, both HTTP 200, 104 rows, 0 changed, 0 removed.
- The catch-up change ledger recorded 16 created listings and 123 field-level changes; no removals.
- `crm_inventory_sheet_reconcile_5m` remains active at `*/5 * * * *`.

Current source and mirror: 104 rows, 87 Available, 17 Rented Out.

## 2. Slack property reconciliation

A direct read-only read of the canonical `Housing_Listings` Sheet returned 104 rows. The Supabase mirror also contains 104 active rows.

Sixteen unique IDs from the 17 Slack confirmations are present in both Sheet and Supabase:

`EF-2611-VN4A`, `EF-2611-G5ZS`, `EF-2611-JBVP`, `EF-2611-ZEFZ`, `EF-2611-6JYX`, `EF-2611-97J4`, `EF-2611-79F1`, `EF-2611-98PS`, `EF-2611-Q2GV`, `EF-2611-WVP3`, `EF-2611-9ZZJ`, `EF-2611-XXHD`, `EF-2611-5NZA`, `EF-2611-KQ44`, `EF-2611-3Q39`, `EF-2611-B42K`.

`EF-2611-NFHV` is not a separate current Sheet row. Its Bellandur 2-BHK, ₹40K rent, 2/5 floor, Nov 15 availability and landmark details are repeated in the later `EF-2611-B42K` entry. B42K adds explicit `Semi Gated` property type and 10 photos. It is treated as the corrected duplicate/re-entry; no second NFHV property was inserted.

### Needs Review state

Eight Slack confirmations initially reported Needs Review. Seven surviving IDs now appear in the canonical Sheet with `status=Pending`, `internal_property_type=Semi Gated`, and empty `error_notes`; NFHV is the duplicate/replaced entry. A full Sheet status scan found no active `Needs Review` rows. The CRM sync did not write to or change the Sheet; it mirrored the current source values. The repository's phase-1 repair script permits a Needs Review-to-Pending transition only after a valid property type and a clean full-row validation, but no execution log was available to attribute these changes to that script.

## 3. Webhook reconciliation repair

### Null-phone failure

The original exception was:

`null value in column "phone" of relation "crm_contact_classifications" violates not-null constraint`

The webhook processor attempted to create a contact classification for a group/newsletter event without a valid personal phone. The database's `phone NOT NULL` constraint remains intact.

### Recovery

- Supabase Edge Function `whapi-crm-webhook` is ACTIVE v10 and routes message persistence through `crm_process_webhook_event`.
- Phone-null events now create `crm_messages` rows with null `classification_id` and null `lead_id`; no fake contact is created.
- `crm_webhook_events.processing_error_history` preserves the original exception before the active error field is cleared.
- Raw event payloads were not rewritten.
- A bounded 500-event batch reconciler backfilled historical processed message events that lacked a `crm_messages` link.
- Since 2026-10-05: 18,621 message events; 18,621 linked; 0 missing message links; 0 current errors.
- Phone-null events since 2026-10-05: 6,641; all linked to messages, 0 contact classifications created.
- Original phone-constraint errors since 2026-10-05: 43; all 43 reconciled and preserved in error history.

## 4. Group-message lead-link repair

A separate audit found historical `@g.us` group messages incorrectly attached to promoted lead timelines.

- 1,809 group-message links were removed across 12 leads and 10 group chats.
- 1,809 `crm_messages` rows remain; their `classification_id` values and message content were not removed.
- Each affected event records the previous lead ID and group chat ID in `reconciliation_history`.
- A batch-level `crm_activity` row records the counts.
- Group messages since 2026-10-05: 13,592; current group messages linked to a lead: 0.
- The deployed SQL and Edge Function path now prevent group messages from attaching to a promoted contact's personal lead timeline. Existing personal contact classifications are not demoted.

## 5. Deterministic qualification

- CRM leads: 371.
- `auto_qualified=true`: 138; `auto_qualified=false`: 233.
- Contact classifications: 839 — 371 promoted, 88 classified, 96 pending, 284 excluded.
- Deterministic scheduler since 2026-10-05: 922 completed / 0 failed; latest observed run 2026-11-12 09:00 UTC.
- Deterministic rules remain independent of AI.
- `crm_ai_scheduler_6h` remains paused; no AI cron trigger was reactivated.

## 6. End-to-end checks

| Path | Evidence | Result |
|---|---|---|
| WhAPI -> webhook event -> message | 18,621/18,621 message events linked | PASS |
| Null-phone/group message -> no fake contact | 6,641 phone-null events; no classification | PASS |
| Group message -> no lead timeline | 0 current group lead links | PASS |
| Original webhook error evidence | 43 original errors retained in history | PASS |
| Slack -> canonical Sheet -> Supabase | 104 source rows / 104 snapshot rows; 16 unique IDs present | PASS with one duplicate/replaced ID |
| Five-minute inventory sync | Consecutive HTTP 200 responses, second run 0 changes | PASS |
| CRM UI root and health | HTTP 200 | PASS |
| Authenticated inventory UI API | Unauthenticated request returns expected HTTP 401; no operator session was used for a live browser data read | Not directly exercised |
| Local browser regression | 1/1 | PASS |

## 7. Repository and release

- Render live commit: `97dff533cfeee3138866277430a471ccc8369ac3`.
- Render deployment: `dep-dbqo57o473hc73881mdg`.
- Supabase Edge Function: v10 ACTIVE.
- Local Node: 24.22.3.
- `npm run build`: PASS.
- `npm test`: 139/139 PASS.
- `npm run test:browser`: 1/1 PASS.
- `npm ci` reported 7 dependency advisories (3 moderate, 4 high); no automatic dependency upgrades were applied.
- The documented Mac checkout and nested CRM worktree are present. The unrelated existing workspace files were preserved.
- At this audit checkpoint, `crm-ui-dashboard` is live and `main` remains at its prior commit pending the post-release fast-forward and tree-equality check.

## 8. Remaining verification boundary

The production root and health endpoints are publicly reachable and return HTTP 200. The inventory API is protected and correctly returns HTTP 401 without an operator session. The live database mirror, source Sheet, server route, and local browser regression were verified; an authenticated production browser session was not used.