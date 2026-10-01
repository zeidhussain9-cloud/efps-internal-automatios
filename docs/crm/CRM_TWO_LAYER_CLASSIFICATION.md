## Current production audit — 2026-10-01 (post-reconciliation)

Verified live state: Render `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, branch `crm-ui-dashboard`, deploy `dep-dauq8hg473hc739ve530`, commit `d28046266239cd889ad14f87a61a92742383305e`. Supabase source `+919148338801`: 186 source-linked leads, 289 classifications, 2 pending, 186 promoted, and 6,621 CRM messages. All 73 webhook events are processed; 0 remain `received`; 0 failed. Automatic reconciliation is active. Browser Realtime is notification-only and CSP allows the exact Supabase HTTPS/WSS origin. RLS is enabled on all CRM tables and `anon`/`authenticated` have no SELECT privilege.

# CRM Two-Layer Classification and Webhook Gate

## Current production behavior — 2026-09-30

The Contact Classification screen is intentionally simple: one queue with two tabs.

- **Not pushed to CRM:** pending and non-qualified contacts.
- **Qualified leads pushed to CRM:** contacts successfully promoted into Lead CRM.

The operator selects one classification and clicks **Update**. A non-qualified choice saves as excluded and remains outside Lead CRM. A **Qualified Lead** choice executes the transactional promotion path and moves the contact only after the database confirms success. Each row includes a direct **Open WhatsApp** link.

The 2026-09-30 production failure was PostgreSQL `42P18` in the new-lead insert. The cause was an untyped `$5` parameter inside `jsonb_build_object()`; the consolidated fix explicitly casts `$5::text`. The operator retry succeeded after deployment.

## Canonical flow

1. WhAPI callback arrives for the connected source `+919148338801`.
2. The Supabase Edge Function authenticates the callback and persists the callback in `crm_webhook_events`.
3. The webhook event is not rejected because the contact is unknown or non-qualified.
4. Message events with a resolvable phone are reconciled into `crm_contact_classifications`.
5. Contact classification is Layer 1: Qualified Lead; Personal / Family; Agent / Partner; Business; Promotion / Marketing; Vendor / Supplier; Internal; Cold Inquiry; Property Listing Sent; Unknown / Pending.
6. Only Qualified Lead is eligible to create/promote a `crm_leads` record.
7. `crm_leads.lead_type` is Layer 2 and describes the operational state of an already-qualified lead.
8. Qualified live messages are appended to `crm_messages` using provider message identity and original message timestamp.
9. Non-qualified contacts remain in the classification/event layers; their events are not promoted into CRM.
10. If a non-qualified contact is later classified as Qualified Lead, the promotion path creates the lead and backfills preserved message events.

## Credential boundary

The WhAPI channel API token is a provider credential. It is not a semantic classifier and is not required by the inbound webhook receiver. The inbound receiver uses a separate webhook authentication secret. Production secret material must not be committed to GitHub or placed in the Render browser/API environment unnecessarily.

## Historical data rule

The historical SQLite archive remains source evidence. It must not be reclassified from aggregate statistics. Current production Supabase records carry their own source and webhook provenance.

## No intake queue

`crm_intake_contacts` / `crm_intake_messages` are not part of this architecture. The classification registry replaces the intake queue.

## Inventory

Inventory sender/source routing is outside this CRM classification path and remains unchanged.
