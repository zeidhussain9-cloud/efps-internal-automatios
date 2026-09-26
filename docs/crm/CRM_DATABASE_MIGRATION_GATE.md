# CRM PostgreSQL deployment gate

**Status (2026-09-26):** Supabase Free project `easyfind-crm` provisioned in Efps, Mumbai (`ap-south-1`), project ref `qttcutwzehtskfcwxkwj`. Schema applied and verified; no customer records imported. Render is still a synthetic preview; its database credential has not been configured.

## Completed
- Nine PostgreSQL tables exist with RLS enabled. No anon/authenticated policies or table grants; database access is intended only through the protected server.
- Three missing foreign-key indexes applied. The performance advisor's remaining unused-index notices are expected on empty tables.
- Core schema and index migrations committed on `crm-ui-dashboard`.
- Parameterized server-side read repository and gated `GET /api/db/status`, `GET /api/db/leads?limit=50` and `GET /api/db/leads/:id` implemented. All require `CRM_DB_READ_ENABLED=true`, `DATABASE_URL` and both Basic Auth credentials; they return 404 while disabled. These endpoints do not write data and the React UI does not yet call them.
- Source Mac SQLite remains untouched. The original 735 leads/23,454 conversation rows and separately curated 308 leads/6,064 message subset still require reconciliation.

## Remaining gates
1. Provision a least-privilege, server-only PostgreSQL connection using Render secret environment configuration. Keep existing Ollama variables intact. Never commit, print or expose the connection string to the browser.
2. Confirm the Render deploy and GitHub CI test results; test the disabled and authenticated database routes with fictional data.
3. Implement durable audited CRUD, provider-event inbox and deduplication, incremental AI cursors, human-override evidence and recovery. D06–D08 remain unapproved.
4. Verify independent encrypted backup and **restore** procedures; Supabase Free must not be treated as the only durable copy of customer conversations.
5. Obtain explicit authorized access to the original SQLite for read-only reconciliation and an import dry-run. Do not use Desktop Commander without authorization.
6. Configure read-only Housing_Listings Sheets access in Render and evaluate existing Ollama settings without reading or replacing secret values.
7. Only after security, backup, migration and design gates pass, authorize live data and WhAPI.

## Boundaries
Slack automation remains the sole writer of `Housing_Listings`; CRM inventory is read-only. Media bytes remain outside PostgreSQL; store Cloudinary URLs only. No automatic WhatsApp send in v1. Migrations are explicit, never invoked on normal web deployment.

**Supabase security notice:** [RLS enabled with no policies](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy) is deliberate for the current server-only model; do not add browser policies without a reviewed authorization design.


## Render credential validation (2026-09-26)

`src/crm-startup-check.mjs` now checks **presence only** for `DATABASE_URL`, `CRM_DB_READ_ENABLED`, both Basic Auth variables, Ollama endpoint/model and Google Sheets credential/ID. It performs a server-side `SELECT 1` probe when `DATABASE_URL` is set and logs only `connected`, `failed` or `not configured`. No credential values or database exception details are logged. Startup probe success alone does not verify least-privilege access, backup readiness or suitability for live customer data. Verify the actual sanitized Render application logs after the new commit deploys. Do not paste credentials into chat.

### Verified Render startup flags — 2026-09-26 17:26 UTC
The live CRM startup diagnostic reported: `DATABASE_URL` absent; `CRM_DB_READ_ENABLED` false; both Basic Auth variables absent; Ollama endpoint and model present; Google Sheets service-account credential and sheet ID absent; `CRM_REAL_DATA_ENABLED` false. Database probe reported `not configured`. These are runtime observations for `easyfind-crm-d01-d05`, not a claim about another service or pending environment edits. Do not enable the DB API or import customer data until the missing server-only settings are configured and a subsequent deployment logs `connected` with authentication configured. Do not copy secret values into documentation or chat.
