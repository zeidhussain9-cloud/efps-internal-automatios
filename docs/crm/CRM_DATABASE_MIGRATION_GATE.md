# CRM PostgreSQL deployment gate

**Status (2026-09-26):** Supabase Free project `easyfind-crm` provisioned in Efps, Mumbai (`ap-south-1`), project ref `qttcutwzehtskfcwxkwj`. Schema applied and verified; no customer records imported. Render remains a synthetic-only preview. At 17:41 UTC the Render startup diagnostic confirmed DATABASE_URL and Basic Auth are present, but its database probe failed. Supabase itself was independently queried successfully.

## Completed
- Nine PostgreSQL tables exist with RLS enabled. No anon/authenticated policies or table grants; database access is intended only through the protected server.
- Three missing foreign-key indexes applied. The performance advisor's remaining unused-index notices are expected on empty tables.
- Core schema and index migrations committed on `crm-ui-dashboard`.
- Parameterized server-side read repository and gated `GET /api/db/status`, `GET /api/db/leads?limit=50` and `GET /api/db/leads/:id` implemented. All require `CRM_DB_READ_ENABLED=true`, `DATABASE_URL` and both Basic Auth credentials; they return 404 while disabled. These endpoints do not write data and the React UI does not yet call them.
- Source Mac SQLite remains untouched. The original 735 leads/23,454 conversation rows and separately curated 308 leads/6,064 message subset still require reconciliation.

## Remaining gates
1. Repair the existing server-only connection from Render to the **already-provisioned Supabase** project; do not create or provision PostgreSQL on Render. The CRM repository now recognizes malformed-but-recoverable Supabase URIs and URL-encodes passwords before using the IPv4-compatible session pooler (port 5432). The remaining proof is the next Render startup: endpoint class must resolve to `supabase_session_pooler_ipv4` and `SELECT 1` must succeed. Keep existing Ollama variables intact. Never commit, print or expose the connection string to the browser.
2. Confirm the Render deploy and GitHub CI test results; test the disabled and authenticated database routes with fictional data.
3. Implement durable audited CRUD, provider-event inbox and deduplication, incremental AI cursors, human-override evidence and recovery. D06–D08 remain unapproved.
4. Verify independent encrypted backup and **restore** procedures; Supabase Free must not be treated as the only durable copy of customer conversations.
5. Obtain explicit authorized access to the original SQLite for read-only reconciliation and an import dry-run. Do not use Desktop Commander without authorization.
6. Reconcile the user's reported full JSON service-account credential and hardcoded sheet ID with the adapter's current expectation of GOOGLE_SERVICE_ACCOUNT_JSON_BASE64, HOUSING_SHEET_ID and HOUSING_SHEET_TAB; verify without printing secrets. Then test read-only Sheets access and existing Ollama settings.
7. Only after security, backup, migration and design gates pass, authorize live data and WhAPI.

## Boundaries
Slack automation remains the sole writer of `Housing_Listings`; CRM inventory is read-only. Media bytes remain outside PostgreSQL; store Cloudinary URLs only. No automatic WhatsApp send in v1. Migrations are explicit, never invoked on normal web deployment.

**Supabase security notice:** [RLS enabled with no policies](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy) is deliberate for the current server-only model; do not add browser policies without a reviewed authorization design.


## Render credential validation (2026-09-26)

`src/crm-startup-check.mjs` now checks **presence only** for `DATABASE_URL`, `CRM_DB_READ_ENABLED`, both Basic Auth variables, Ollama endpoint/model and Google Sheets credential/ID. It performs a server-side `SELECT 1` probe when `DATABASE_URL` is set and logs only `connected`, `failed` or `not configured`. No credential values or database exception details are logged. Startup probe success alone does not verify least-privilege access, backup readiness or suitability for live customer data. Verify the actual sanitized Render application logs after the new commit deploys. Do not paste credentials into chat.

### Historical startup checkpoint — superseded (17:26 UTC)
The 17:26 UTC absence observations are retained only as history. They are not current configuration guidance.

### Latest verified runtime checkpoint — 2026-09-26 17:41 UTC
Render startup reported databaseUrlPresent=true, databaseReadOptIn=true, authConfigured=true, authIncomplete=false, ollamaEndpointPresent=true, ollamaModelPresent=true, sheetsCredentialPresent=false, sheetsIdPresent=false and liveDataEnabled=false. The Supabase project qttcutwzehtskfcwxkwj was independently confirmed ACTIVE_HEALTHY and SELECT succeeded; nine public tables exist. Render's database connectivity probe failed with details withheld, so the cause is **not yet proven**. No Render-hosted PostgreSQL is required. The Sheets flags inspect only the adapter's expected environment variable names, not every possible user-provided raw JSON variable or a hardcoded sheet ID; do not conclude the user has not supplied credentials. Do not expose secret values or enable live customer data.
