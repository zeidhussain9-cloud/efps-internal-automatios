# CRM PostgreSQL deployment gate

**Status (2026-09-26):** Supabase Free project `easyfind-crm` provisioned in Efps, Mumbai (`ap-south-1`), project ref `qttcutwzehtskfcwxkwj`. Schema applied and verified; no customer records imported. Render remains a synthetic/empty-database preview. At 18:55 UTC the Render startup diagnostic confirmed the Supabase session-pooler endpoint, server-only CA, Basic Auth and the DB `SELECT 1` probe successfully.

## Completed
- Nine PostgreSQL tables exist with RLS enabled. No anon/authenticated policies or table grants; database access is intended only through the protected server.
- Three missing foreign-key indexes applied. The performance advisor's remaining unused-index notices are expected on empty tables.
- Core schema and index migrations committed on `crm-ui-dashboard`.
- Parameterized server-side read repository and gated `GET /api/db/status`, `GET /api/db/leads?limit=50` and `GET /api/db/leads/:id` implemented. All require `CRM_DB_READ_ENABLED=true`, `DATABASE_URL` and both Basic Auth credentials; they return 404 while disabled. These endpoints do not write data and the React UI does not yet call them.
- Source Mac SQLite remains untouched. The original 735 leads/23,454 conversation rows and separately curated 308 leads/6,064 message subset still require reconciliation.

## Remaining gates
1. [x] Repair and verify the existing server-only Render→Supabase connection; endpoint class is `supabase_session_pooler_ipv4`, the Supabase CA is configured server-side, and `SELECT 1` succeeds. Keep the connection string out of source, browser and logs.
2. [x] Confirm the Render deploy and GitHub CI test results. [ ] Test the authenticated database routes against the empty schema with operator credentials.
3. Implement durable audited CRUD, provider-event inbox and deduplication, incremental AI cursors, human-override evidence and recovery. D06–D08 remain unapproved.
4. Verify independent encrypted backup and **restore** procedures; Supabase Free must not be treated as the only durable copy of customer conversations.
5. Obtain explicit authorized access to the original SQLite for read-only reconciliation and an import dry-run. Do not use Desktop Commander without authorization.
6. [x] Verify the canonical Sheet ID/tab contract against `shared/google_sheets/schema.py` without printing secrets; the CRM adapter consumes the Sheet ID from Render rather than hardcoding it. [ ] Verify the server-side Sheets credential and test read-only access; existing Ollama endpoint/model presence is confirmed, but a synthetic provider request remains unexecuted.
7. Only after security, backup, migration and design gates pass, authorize live data and WhAPI.

## Boundaries
Slack automation remains the sole writer of `Housing_Listings`; CRM inventory is read-only. Media bytes remain outside PostgreSQL; store Cloudinary URLs only. No automatic WhatsApp send in v1. Migrations are explicit, never invoked on normal web deployment.

**Supabase security notice:** [RLS enabled with no policies](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy) is deliberate for the current server-only model; do not add browser policies without a reviewed authorization design.


## Render credential validation (2026-09-26)

`src/crm-startup-check.mjs` now checks **presence only** for `DATABASE_URL`, `CRM_DB_READ_ENABLED`, both Basic Auth variables, Ollama endpoint/model and Google Sheets credential/ID. It performs a server-side `SELECT 1` probe when `DATABASE_URL` is set and logs only `connected`, `failed` or `not configured`. No credential values or database exception details are logged. Startup probe success alone does not verify least-privilege access, backup readiness or suitability for live customer data. Verify the actual sanitized Render application logs after the new commit deploys. Do not paste credentials into chat.

### Historical startup checkpoint — superseded (17:26 UTC)
The 17:26 UTC absence observations are retained only as history. They are not current configuration guidance.

### Latest verified runtime checkpoint — 2026-09-26 18:55 UTC
Render startup reports databaseUrlPresent=true, databaseReadOptIn=true, databaseTlsCaPresent=true, authConfigured=true, authIncomplete=false, ollamaEndpointPresent=true, ollamaModelPresent=true, sheetsCredentialPresent=false, sheetsIdPresent=true and liveDataEnabled=false. The Supabase project qttcutwzehtskfcwxkwj was independently confirmed ACTIVE_HEALTHY and SQL succeeded; nine public CRM tables exist. Render classifies the endpoint as `supabase_session_pooler_ipv4` and the startup DB probe reports `connected`. The database remains empty of customer rows. Do not expose secret values or enable live customer data.


## 2026-09-26 18:55 UTC connection verification
- [x] Render uses the IPv4-compatible Supabase session pooler on port 5432.
- [x] Server-side Supabase CA is configured through DATABASE_SSL_CA with certificate verification enabled; TLS failure SELF_SIGNED_CERT_IN_CHAIN is resolved without disabling verification.
- [x] Startup SELECT 1 succeeds and diagnostics remain secret-safe.
- [ ] Authenticated application-level DB route verification remains to be exercised with operator credentials; this is separate from startup connectivity.


## Durability v2 verification — 2026-09-27
- [x] Migration 002 applied to Supabase and recorded in crm_schema_migrations (versions 1, 2).
- [x] Five new tables verified: crm_provider_events, crm_ai_cursors, crm_requirement_evidence, crm_idempotency_keys and crm_property_media.
- [x] Append-only triggers verified for messages, activity, requirement evidence and property actions; lead updated_at trigger present.
- [x] Post-migration counts: zero leads, messages, provider events and requirement evidence. No customer data imported.
- [x] GitHub Actions #116 passed build, unit/integration tests and Chromium browser journey.
- [ ] Verify authenticated application-level read routes, test transaction-safe writes against an isolated test database, and independently restore an encrypted backup before any production write enablement.
- [ ] Keep CRM_DB_WRITE_ENABLED and CRM_REAL_DATA_ENABLED disabled pending production auth, historical reconciliation and D06–D08 approval.
