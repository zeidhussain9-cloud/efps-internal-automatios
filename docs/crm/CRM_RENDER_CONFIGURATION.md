# CRM deployment configuration — staged setup

The CRM Render service is `easyfind-crm-d01-d05`, deployed only from `crm-ui-dashboard`. Do not configure the old leads UI or main branch. Keep secrets out of GitHub, the React bundle, chat transcripts and logs.

## Current stage: synthetic-only

The browser prototype contains fictional leads and properties. Its versioned browser storage survives reloads **on the same browser**; it is not a secure production database and does not synchronize across devices. Server authentication can be enabled with the two variables below. Until both are set, the preview remains public and MUST NOT receive real customer records. If exactly one is set, the server fails closed.

| Variable | Purpose |
| --- | --- |
| `CRM_BASIC_AUTH_USERNAME` | Operator login name |
| `CRM_BASIC_AUTH_PASSWORD` | Unique high-entropy operator password |

The public `/health` endpoint reports only synthetic mode and access mode, never secret values. Authentication is a temporary pilot gate, not the final production user/session architecture. Use HTTPS and do not reuse a password from another service.

## Ollama configuration — later gate

The operator has stated the Ollama API key and model name have already been placed in a Render environment. A server-only adapter and authenticated fictional-fixture route are implemented but disabled by default. **Inspect the variable names and target service without revealing their values**, then adapt the server-side provider configuration to those names. Do not overwrite existing credentials, infer an endpoint from a model name, expose the API key to the browser or claim the provider is connected until a synthetic request succeeds. Ollama local `localhost` endpoints on Render refer to Render, not the operator's Mac. If using an external provider, verify its exact base URL and API protocol. Restrict model input to fictional pilot records until the live-data gate is approved. The adapter accepts `OLLAMA_BASE_URL` (or `OLLAMA_HOST`), `OLLAMA_MODEL` (or `OLLAMA_MODEL_NAME`) and optional `OLLAMA_API_KEY`; map existing names without duplicating secrets. Only set `CRM_SYNTHETIC_AI_ENABLED=true` after server access credentials are active and the endpoint is verified. The route accepts only the four fictional fixture IDs and never client-supplied conversations.

## Read-only Google Sheets configuration — later gate

The existing Slack integration owns creation and updates of Housing Listings. CRM must only read the existing sheet and preserve its editor audit trail. Once ready, provide these **server-only** values in the same Render service:

| Variable | Purpose |
| --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | Base64 of the entire service-account JSON, not the private key alone |
| `HOUSING_SHEET_ID` | Spreadsheet ID of the verified Housing Listings document |
| `HOUSING_SHEET_TAB` | Exact verified worksheet name, expected `Housing_Listings` unless source differs |

A read-only service-account adapter is implemented and disabled by default with `CRM_SYNTHETIC_SHEETS_ENABLED` (unset). Do not enable it until the intended real sheet and access policy are approved. Grant the service-account email **Viewer** access to the verified spreadsheet. Do not give it Editor access or share the JSON publicly. The CRM must not write to the sheet or create a competing inventory workflow. Base64 is transport encoding, not encryption; treat it as a secret. Do not configure any real sheet access until the synthetic pilot and access gate are verified.

## Release checks

1. GitHub Actions: `npm test`, `npm run build`, Chromium browser journey.
2. Render: latest commit is live; `/health` reports synthetic mode and intended access mode.
3. Synthetic editing survives reloads; follow-ups, per-lead overrides, filtering and error states pass browser checks.
4. Authenticated access gate verified before any real data. Production durable storage requires a separately approved persistent database and backups; Render free ephemeral filesystem is not sufficient.
5. Only then connect existing Ollama settings and read-only Sheets credentials, test with fictional data and separately approve real SQLite migration.

No live WhAPI ingestion, automatic WhatsApp sending or live customer data is enabled by this document.
