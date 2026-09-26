# CRM PostgreSQL deployment gate

**State:** Schema and migration tests committed; no database provisioned or migrated. The existing Render workspace has no PostgreSQL instance. This document does not authorize creating a paid resource or importing real records.

## Deployment requirements

- Provision an appropriately sized **persistent** PostgreSQL instance with an agreed backup/restore policy. A free or ephemeral database without suitable backup/retention is not sufficient for the only copy of customer conversations.
- Use the internal/private database URL in Render server-only `DATABASE_URL`. Do not place it in the React bundle, GitHub, browser storage or logs.
- Configure production session authentication before any customer import. The current Basic Auth gate is a temporary fictional pilot control, not a multi-device session system.
- Explicitly set `CRM_MIGRATION_APPROVED=true` only for a reviewed one-off migration, then run `npm run db:migrate` in an authorized environment. The web server and normal Render build **never** run migrations automatically. Leave `CRM_REAL_DATA_ENABLED` unset during schema setup.
- Verify schema, row-level application permissions, backup restoration and audit append behavior using fictional fixtures before importing customers.

## Historical import gate

The previously observed original Mac SQLite extraction contained 735 leads and 23,454 messages from the three verified source numbers, whereas a separately curated audit subset contained 308 leads and 6,064 messages. These populations are not interchangeable. Reconcile authoritative scope, per-source counts, message IDs, time bounds and classification provenance before importing. Do not rerun the old importer in place because it may overwrite edited leads or duplicate conversations.

`src/historical-import-plan.mjs` provides pure normalization and deduplication planning, with no database connection or customer data access. The PostgreSQL `crm_messages` unique constraint on (source_number,provider_message_id) provides a second deduplication barrier. Actual ETL, dry-run comparison, resumability and operator-edit preservation remain pending.

## Separation of responsibilities

- CRM owns leads, messages, follow-ups, operator activity, AI proposals, WhatsApp draft versions and per-lead property actions.
- Slack automation remains the **only** inventory writer. The CRM later reads `Housing_Listings` with a Viewer service account. Do not copy live inventory into a competing editable store.
- Ollama API credentials and the Google service-account JSON remain server-only in Render; never print their values. WhAPI ingestion starts only after the historical migration gate and one final deduplicated gap extraction.
