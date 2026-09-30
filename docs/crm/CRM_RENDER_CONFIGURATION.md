## Current production audit — 2026-10-01 (post-reconciliation)

Verified live state: Render `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, branch `crm-ui-dashboard`, deploy `dep-daum9vi1a91c739kcfhg`, commit `866dd78b594032eadff9f2a771cb170e7b41aded`. Supabase source `+919148338801`: 185 source-linked leads, 288 classifications, 13 pending, 2 explicitly unqualified/excluded, 185 promoted, and 6,594 CRM messages. All 46 webhook events are now processed; 0 remain `received`; 0 failed. The 33-event operational backlog has therefore been reconciled. Browser Realtime is notification-only and CSP allows the exact Supabase HTTPS/WSS origin. RLS is enabled on all CRM tables and `anon`/`authenticated` have no SELECT privilege. Render reports Basic Auth configured and database connectivity connected.

## Current production checkpoint — 2026-10-01

Render service `easyfind-crm-d01-d05` (`srv-darsv560tbcc73cu4ip0`) deploys `crm-ui-dashboard`. Current deployed commit is `45dbab7b1ba92387e5e001f74929ad40c92be6a9` and the corresponding Render deploy is live. Supabase project `qttcutwzehtskfcwxkwj` is the CRM operational database.

Current source: `+919148338801`. The other configured source numbers `+917975102130` and `+919902024973` are visible/selectable in the UI only and are not active production ingestion sources.

Current production database state: 185 source-linked leads, 288 classifications, 13 pending classifications, 185 qualified classifications, 6,561 messages, and 46 webhook events (13 processed, 33 received, 0 failed). The 33 received events are an operational reconciliation backlog.

The browser Realtime channel is a UI refresh signal, not the webhook source of truth. The latest hardening change explicitly allows the exact Supabase HTTPS/WSS origin in the server CSP so the browser Realtime client is not blocked by the previous `connect-src 'self'` restriction.


# CRM deployment configuration — staged setup

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

## 2026-09-27 — Hosted Ollama verified; dedicated steering

The historical 'later gate' instructions above predate the successful Render fictional request. At 2026-09-26 21:25:38 UTC, Render logged a successful `gpt-oss:20b` fictional analysis returning the five required fields. `OLLAMA_BASE_URL`, `OLLAMA_MODEL` and `OLLAMA_API_KEY` are server-side Render settings; never print or copy credential values into Git, browser bundles or logs. The model is hosted: **do not install it locally**.

The root `steering.md` is the dedicated executable CRM model instruction; the adapter caches it and enforces a 2-KiB maximum. The operator-only `CORE_STEERING.md` and complete `docs/BUSINESS_CONTEXT.md` are not sent to the provider. AI remains assistive and does not send WhatsApp messages. Current production CRM writes/read paths are protected server-side; real CRM data is active for `+919148338801`.

## 2026-09-30 — Current production CRM UI deployment

`crm-ui-dashboard` is the canonical CRM UI development/deployment branch. Render `easyfind-crm-d01-d05` auto-deploys this branch. Local checkout and GitHub `origin/crm-ui-dashboard` are reconciled to the same commit. The production source currently in scope is `+919148338801`; historical and live WhatsApp records reconcile through Supabase. The other configured source numbers remain visible in the UI but are not imported into the current production flow.

## Classification write gate — 2026-09-30

Production classification updates require protected CRM access, DATABASE_URL, and an enabled classification/database write gate. The preferred dedicated gate is CRM_CLASSIFICATION_WRITE_ENABLED=true; CRM_DB_WRITE_ENABLED=true remains accepted as the compatibility gate until the Render environment is explicitly migrated.

- protected CRM authentication;
- DATABASE_URL;
- CRM_CLASSIFICATION_WRITE_ENABLED=true;
- server-side transactional classification repository.

The browser cannot write directly to Supabase. A successful Qualified Lead update creates/links the CRM lead and links preserved messages in the same server-side transaction before the UI moves the contact to the promoted queue.

Render environment-variable changes require a redeploy before the running service uses the new value.


## 2026-10-01 — D07 runtime configuration closure

The Render CRM service continues to deploy `crm-ui-dashboard`. The existing configured CRM operator credential is verified through the application sign-in endpoint; successful sign-in creates an opaque HttpOnly `efps_crm_session` cookie. Session policy is 8 hours of inactivity and 12 hours maximum. No credential values are stored in source or emitted in logs. UI privacy masking, reversible archive/restore, audit visibility, explicit CSV export and offline/write gating are application controls and do not require new secret values.


## 2026-10-01 — mobile/Reatime production checkpoint

Latest verified deployment: Render `easyfind-crm-d01-d05`, deploy `dep-daupehaj7g8c73a5rgl0`, commit `78ab084cf3470d4b04d304a312ec09d40fcbe0f6`, status **live**.

Mobile/compact layout is now covered by a 1000px responsive shell and the browser regression includes a 900px compact-viewport assertion. The Supabase browser client is configured from Render build variables `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`. The Realtime subscription is initialized after operator sign-in; the previous mount-only effect caused the UI to remain `unconfigured` after authentication even when browser configuration existed.

Production Supabase verification confirms the `crm_messages_realtime_broadcast` trigger exists on `public.crm_messages` and invokes `crm_broadcast_message_activity`. Realtime is notification-only; the protected CRM API remains the source of displayed data.

CI run **#284** for this revision is green: build, full test suite, Chromium installation and browser E2E all passed.
