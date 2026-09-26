# CRM deployment configuration — staged setup

The CRM Render service is `easyfind-crm-d01-d05`, deployed only from `crm-ui-dashboard`. Do not configure the old leads UI or main branch. Keep secrets out of GitHub, the React bundle, chat transcripts and logs.

## Current verified stage: synthetic-only with empty Supabase connection (2026-09-26 18:55 UTC)

The browser prototype contains fictional leads and properties. Its versioned browser storage survives reloads **on the same browser**; it is not a secure production database and does not synchronize across devices. Basic Auth was confirmed configured at the latest Render startup, but it is still a temporary pilot gate. Real customer records remain disabled pending the migration and security gates. If exactly one is set, the server fails closed.

| Variable | Purpose |
| --- | --- |
| `CRM_BASIC_AUTH_USERNAME` | Operator login name |
| `CRM_BASIC_AUTH_PASSWORD` | Unique high-entropy operator password |

The public `/health` endpoint reports only `{ "ok": true }`; it does not disclose access mode or configuration. Authentication is a temporary pilot gate, not the final production user/session architecture. Use HTTPS and do not reuse a password from another service.

## Ollama configuration — later gate

The operator has stated the Ollama API key and model name have already been placed in a Render environment. A server-only adapter and authenticated fictional-fixture route are implemented but disabled by default. **Inspect the variable names and target service without revealing their values**, then adapt the server-side provider configuration to those names. Do not overwrite existing credentials, infer an endpoint from a model name, expose the API key to the browser or claim the provider is connected until a synthetic request succeeds. Ollama local `localhost` endpoints on Render refer to Render, not the operator's Mac. If using an external provider, verify its exact base URL and API protocol. Restrict model input to fictional pilot records until the live-data gate is approved. The adapter accepts `OLLAMA_BASE_URL` (or `OLLAMA_HOST`), `OLLAMA_MODEL` (or `OLLAMA_MODEL_NAME`) and optional `OLLAMA_API_KEY`; map existing names without duplicating secrets. Only set `CRM_SYNTHETIC_AI_ENABLED=true` after server access credentials are active and the endpoint is verified. The route accepts only the four fictional fixture IDs and never client-supplied conversations.

## Read-only Google Sheets — credential-format reconciliation pending

The existing Slack integration owns creation and updates of Housing Listings. CRM must only read the existing sheet and preserve its editor audit trail. The operator reports already adding the **full JSON service account** and hardcoding the sheet ID. The adapter now accepts the existing repository credential names (`GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_APPLICATION_CREDENTIALS`) as well as the CRM-specific Base64 name. The latest Render runtime detects the Sheet ID but not a Sheets credential. The database connection blocker is resolved: Render recognizes the Supabase session pooler and the startup DB probe succeeds with the configured server-only CA. Do not print or overwrite existing credentials. Current adapter inputs:

| Variable | Purpose |
| --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | Base64 of the entire service-account JSON, not the private key alone |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Existing legacy raw JSON credential name; accepted server-side |
| `GOOGLE_APPLICATION_CREDENTIALS` | Existing legacy credential environment name; accepted server-side |
| `HOUSING_SHEET_ID` | Spreadsheet ID of the verified Housing Listings document |
| `HOUSING_SHEET_TAB` | Exact verified worksheet name, expected `Housing_Listings` unless source differs |
| `DATABASE_SSL_CA` | Public Supabase root CA certificate used server-side for strict TLS verification |

A read-only service-account adapter is implemented and disabled by default with `CRM_SYNTHETIC_SHEETS_ENABLED`; it reads only `A:AT` so reserved `AU`/`AV` columns are never consumed. It accepts the repository's legacy raw JSON environment names in addition to the CRM-specific Base64 form, plus a sheet ID and tab name. The canonical Sheet ID is intentionally maintained in `shared/google_sheets/schema.py`; the CRM adapter does not duplicate or hardcode it and instead consumes `HOUSING_SHEET_ID`/`SHEET_ID` from Render. Do not enable it until the intended real sheet and access policy are approved. Grant the service-account email **Viewer** access to the verified spreadsheet. Do not give it Editor access or share the JSON publicly. The CRM must not write to the sheet or create a competing inventory workflow. Base64 is transport encoding, not encryption; treat it as a secret. Do not configure any real sheet access until the synthetic pilot and access gate are verified.

## Release checks

1. GitHub Actions: `npm test`, `npm run build`, Chromium browser journey.
2. Render: latest commit is live; `/health` returns only `{ "ok": true }` and hardened security headers are present.
3. Synthetic editing survives reloads; follow-ups, per-lead overrides, filtering and error states pass browser checks.
4. Authenticated access gate and Supabase connection are verified before any real data. Supabase `easyfind-crm` is the sole hosted CRM database; no Render PostgreSQL service is required. Render uses the IPv4-compatible session pooler URL on port 5432 with strict TLS verification via `DATABASE_SSL_CA`. Independent backup and restore testing remain required.
5. Only then connect existing Ollama settings and read-only Sheets credentials, test with fictional data and separately approve real SQLite migration.

No live WhAPI ingestion, automatic WhatsApp sending or live customer data is enabled by this document.

## Latest connection audit — 2026-09-26 18:55 UTC
- Supabase project `qttcutwzehtskfcwxkwj` ACTIVE_HEALTHY; independent SQL query succeeded; nine public tables.
- Render DATABASE_URL, CRM_DB_READ_ENABLED, Basic Auth, Ollama endpoint/model and `DATABASE_SSL_CA` present; database endpoint classified as the Supabase session pooler and the `SELECT 1` probe succeeds.
- Google Sheets startup flags check only GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 and HOUSING_SHEET_ID, not alternative raw JSON names or source-level hardcoding. Operator reports providing full JSON and hardcoded ID; verify mapping rather than requesting new secrets.
- `CRM_REAL_DATA_ENABLED` remains false. Do not provision PostgreSQL on Render or import customer records until the remaining durable-auth, backup, historical-reconciliation and D06–D08 safety gates pass.


## 2026-09-26 canonical inventory contract verification
- [x] Canonical spreadsheet ID verified in `shared/google_sheets/schema.py`.
- [x] Canonical worksheet verified as `Housing_Listings`.
- [x] CRM adapter keeps the spreadsheet ID out of application source and reads it from server-side configuration.
- [ ] Real service-account credential is present in Render (current runtime flag: false) and read-only Sheets access has not yet been exercised.
