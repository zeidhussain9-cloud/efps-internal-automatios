## Current UI-polish verification checkpoint — 2026-10-02

This is an **unreleased candidate checkpoint** for `crm-ui-polish-final-2026-10-02`. It must not be described as production until it is merged to `crm-ui-dashboard`, deployed by Render, and production-verified.

- **Implementation branch:** `crm-ui-polish-final-2026-10-02`
- **Production baseline:** `crm-ui-dashboard` @ `510c62304751624a9e118db137fa4b9095d61bc9`
- **Current production Render:** `easyfind-crm-d01-d05` is still LIVE from `crm-ui-dashboard` @ `510c62304751624a9e118db137fa4b9095d61bc9`
- **Latest candidate code checkpoint:** `b20587e57105f7db27aeeda3714eb0a4cfe55a7b`
- **Candidate verification:** GitHub Actions run #22 passed `npm run build`, `npm test` (84/84), and `npm run test:browser` (1/1) using Node.js 24.21.0.
- **Implemented in candidate:** stable direct CRM routes and lead deep links, browser-history/tab routing, debounced lead search, restored verified desktop layout foundations, consolidated UI polish/responsive/accessibility styling, and route/browser regression coverage.
- **Backend boundary:** no backend source/API contract changes were made by this UI candidate relative to the production baseline. Webhook ingestion, Supabase persistence/reconciliation, classification, AI, inventory data logic, authentication, privacy, and audit backend paths remain on the production baseline.
- **Replit artifacts:** the accidental Replit workspace artifact and Replit-specific `.replit` configuration were not carried into the candidate branch.
- **Node runtime:** the candidate pins Node.js 24.21.0 via `.node-version` and a bounded package engine range. Render documents 24.21.0 as the current default for services created on or after 2026-09-17 and documents `.node-version`/package engines as supported version controls.
- **Status:** candidate verification is GREEN in CI; production deployment and production browser verification are still pending.
- **Documentation rule:** this checkpoint supersedes neither the older production closure evidence nor the historical sections below; after production merge/deploy, this block must be updated with the actual deployed commit/deployment and tree-equality evidence.

## Current production audit — 2026-10-01 (post-reconciliation)

## Authoritative current closure — 2026-10-01

Evidence snapshot after final verification:
- crm-ui-dashboard commit: 252dad9e029d9c3d3ee8bd93be20c171f4099602
- crm-ui-dashboard tree: 375a701d907830a04ddd5f6d517f982ea729ed68
- main reconciliation commit: 918a9b9d1f010c144b400b01d23bad26ee061fb9
- main tree: 375a701d907830a04ddd5f6d517f982ea729ed68
- tree(main) == tree(crm-ui-dashboard): TRUE
- Render deployment: dep-dav82h3m8hqs7399j4ug, status LIVE, commit 1c196577fc414be52c8fc889b3886f11e0e9da5d
- Production health: GET /health = HTTP 200, {"ok":true}
- Supabase: 186 leads, 6,870 messages, 465 webhook events, 310 classifications, 186 requirements, 196 AI runs, 196 drafts, 186 cursors, 88 active inventory rows
- Webhook events: 465/465 processed; 0 received; 0 processing; 0 failed
- Message reconciliation: 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0
- Historical classification population: 228/228 source="historical_extract"; 140/140 qualified mappings resolve to promoted leads
- Requirements: 186/186 lead rows have requirement rows; orphan/missing = 0
- AI/drafts: 196/196 draft→AI-run lead mappings valid; stale evidence references = 0; invalid cursor lead links = 0
- Inventory: 88 active rows; 71 Available; 17 Rented Out; invalid media-array rows = 0
- Cloudinary: 829/829 distinct production URLs returned HTTP 200 with image/* content-type using direct HEAD checks from the production-machine network path
- Tests: npm run build PASS; npm test 78/78 PASS; npm run test:browser 1/1 PASS
- Supabase Edge Function whapi-crm-webhook: ACTIVE version 8
- Legacy AWS webhook/handler files: no changes in the CRM hardening commit range
- 24-item audit status: GREEN / VERIFIED

Historical dated checkpoints below remain historical evidence; this block is the current source of truth.


> Current authoritative release note: the verified production release is crm-ui-dashboard commit 1c196577fc414be52c8fc889b3886f11e0e9da5d, Render deployment dep-dav82h3m8hqs7399j4ug (LIVE).

See the authoritative current-state block at the top of this document for the verified Render/Supabase checkpoint.

## Current production checkpoint — 2026-10-01

Render service `easyfind-crm-d01-d05` (`srv-darsv560tbcc73cu4ip0`) deploys `crm-ui-dashboard`; the synchronized release is **live**. Supabase project `qttcutwzehtskfcwxkwj` is the CRM operational database.

Current source: `+919148338801`. The other configured source numbers `+917975102130` and `+919902024973` are visible/selectable in the UI only and are not active production ingestion sources.

Current production database state: 186 leads, 310 classifications, 23 pending classifications, 186 promoted classifications, 6,870 messages, and 465 webhook events (465 processed, 0 received, 0 processing, 0 failed).

The browser Realtime channel is a UI refresh signal, not the webhook source of truth. The latest hardening change explicitly allows the exact Supabase HTTPS/WSS origin in the server CSP so the browser Realtime client is not blocked by the previous `connect-src 'self'` restriction.


# CRM deployment configuration — staged setup

## Authoritative current verified state — 2026-10-01 21:55 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **CRM commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **CRM tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **main:** `b2fbf366021852aedd4bf0ec66484ad421fb5662`
- **main tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** `dep-dav82h3m8hqs7399j4ug` = **LIVE**
- **Live Render commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 186 leads; 6,870 messages; 465 webhook events; 310 classifications; 186 requirements; 196 AI runs; 196 drafts; 186 AI cursors; 88 active inventory rows.
- **Classification status:** 186 promoted; 88 classified; 23 pending; 13 excluded = 310 total.
- **Webhook status:** 465 processed; 0 received; 0 processing; 0 failed.
- **Message reconciliation:** 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 829/829 distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 78/78 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v8.
- **AWS legacy webhook:** no changes in the audited CRM hardening range.
- **24-item CRM audit:** GREEN / VERIFIED.

### Current operational flow

```text
WhAPI +919148338801
  -> crm_webhook_events (persist + deduplicate)
  -> webhook processor/reconciler
  -> crm_messages + classification registry
  -> operator classification update
       -> non-qualified: remains outside CRM leads
       -> Qualified Lead: audited promotion transaction
            -> crm_leads + preserved messages
            -> webhook event lead linkage reconciled

CRM lead workspace
  -> complete chronological conversation + normalized requirements + evidence + notes + prior AI runs + cursor
  -> Bedrock primary / Sonnet fallback / Ollama fallback
  -> persisted crm_ai_runs + crm_drafts + provenance
  -> operator review/edit/pre-send grounding
  -> manual WhatsApp action only; no automatic send

Housing_Listings A:AV
  -> CRM reads operational A:AT only
  -> 88-row operational mirror in crm_inventory_snapshot
  -> five-minute reconciliation
  -> crm_inventory_sync_changes records future field-level changes
```

### Test-history checkpoint

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The final repository verification was 71/71 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.



# CRM deployment configuration — staged setup

The CRM Render service is `easyfind-crm-d01-d05`, deployed only from `crm-ui-dashboard`. Do not configure the old leads UI or main branch. Keep secrets out of GitHub, the React bundle, chat transcripts and logs.

## Historical staged setup — superseded 2026-09-26

The browser prototype contains fictional leads and properties. Its versioned browser storage survives reloads **on the same browser**; it is not a secure production database and does not synchronize across devices. Basic Auth was the temporary authentication mechanism at this historical checkpoint; the current production UI uses the reviewed operator session flow. Real customer data is now active in the source-scoped Supabase CRM path. If exactly one is set, the server fails closed.

| Variable | Purpose |
| --- | --- |
| `CRM_BASIC_AUTH_USERNAME` | Operator login name |
| `CRM_BASIC_AUTH_PASSWORD` | Unique high-entropy operator password |

The public `/health` endpoint reports only `{ "ok": true }`; it does not disclose access mode or configuration. The historical Basic Auth gate described in this section is superseded by the current operator session architecture. Use HTTPS and do not reuse a password from another service.

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

At this historical checkpoint, live WhAPI ingestion and live customer data were not yet enabled. The current production path is documented in the 2026-10-01 checkpoint above; automatic WhatsApp sending remains disabled.

## Latest connection audit — 2026-09-26 18:55 UTC
- Supabase project `qttcutwzehtskfcwxkwj` ACTIVE_HEALTHY; independent SQL query succeeded; nine public tables.
- Render DATABASE_URL, CRM_DB_READ_ENABLED, Basic Auth, Ollama endpoint/model and `DATABASE_SSL_CA` present; database endpoint classified as the Supabase session pooler and the `SELECT 1` probe succeeds.
- Google Sheets startup flags check only GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 and HOUSING_SHEET_ID, not alternative raw JSON names or source-level hardcoding. Operator reports providing full JSON and hardcoded ID; verify mapping rather than requesting new secrets.
- `CRM_REAL_DATA_ENABLED` is retained as a migration/import safety guard; its historical `false` state did not prevent the later source-scoped webhook/classification production path. Do not treat this variable alone as the current live-data status.


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

## 2026-10-01 — Leads Inbox production data fields

The protected /api/db/leads response now includes contacted_at, last_message_direction, and last_message_at, derived from stored crm_messages with the existing (lead_id,message_at,id) index. The production source currently has 186 source-linked leads; a direct Supabase verification found 186 with at least one Incoming/customer message and 178 with at least one Outgoing message.

Render deployment continues from crm-ui-dashboard. The browser displays the three timeline fields in Asia/Kolkata as DD-Month-YYYY / HH:MM, and the lead_sort request parameter controls server-side ordering.

## 2026-10-01 production AI configuration

Render service `srv-darsv560tbcc73cu4ip0` is the production CRM service and deploys branch `crm-ui-dashboard`. The production implementation uses the server-side Ollama adapter for authenticated lead analysis. `CRM_REAL_AI_ENABLED=true` and `CRM_DB_WRITE_ENABLED=true` have been enabled on this service; existing secrets were preserved because the environment update was a merge, not a replacement.

The AI route builds its model input from the complete stored lead workspace: chronological CRM messages, normalized requirements, field-level requirement evidence, operator notes, prior AI runs and the per-lead cursor. AI produces a proposed requirement delta, evidence, timeline analysis, suggested lead status and an operator-editable reply draft. Requirement changes require explicit operator acceptance. Drafts are versioned and are never automatically sent to WhatsApp.


## 2026-10-01 — Bedrock primary / Ollama fallback configuration

The production CRM AI provider order is now AWS Bedrock first, Ollama second. Render service `easyfind-crm-d01-d05` is configured with non-secret Bedrock settings: `AWS_REGION=ap-southeast-2`, `AWS_BEDROCK_MODEL_ID=au.anthropic.claude-opus-4-6-v1`, `AWS_BEDROCK_MAX_TOKENS=4096`, and `AWS_BEDROCK_TEMPERATURE=0.2`. The application uses the AWS SDK default credential chain, so AWS credentials must be provided to Render as protected environment variables or an equivalent runtime identity; local Mac profiles are not inherited by Render. The existing Ollama configuration remains the fallback and no-auto-send/operator approval controls are unchanged.

## 2026-10-01 — Current Bedrock runtime
Production provider order is AWS Bedrock Claude Opus 4.6 followed by Ollama gpt-oss:20b. Render holds AWS credentials as secrets; non-secret region/model configuration is ap-southeast-2 / au.anthropic.claude-opus-4-6-v1.

## 2026-10-01 — Current draft provenance/runtime checkpoint

Production migration 16 adds AI provenance to `crm_drafts`: `ai_run_id`, `ai_provider`, and `model_name`. Render continues to use Bedrock Claude Opus 4.6 as primary and Ollama gpt-oss:20b as fallback. AWS credentials are currently stored as Render secrets using the operator-approved temporary broad identity; least-privilege credential rotation remains an explicit hardening item.

## 2026-10-01 — Bedrock fallback and AI operator controls

The production Bedrock chain is now **Claude Opus 4.6 (`au.anthropic.claude-opus-4-6-v1`) → Claude Sonnet 4.6 (`au.anthropic.claude-sonnet-4-6`) → Ollama `gpt-oss:20b`**. The Sonnet fallback was selected after a direct tone audition against the tested lead: it produced a concise, accountable re-engagement draft without unsupported inventory claims, and its AU inference profile preserves the existing Australia/NZ geographic routing. Claude Opus 4.5 was also directly invokable through the global profile and produced a strong draft, but AWS documents no AU geo profile for Opus 4.5, so it is not used as the production fallback for this CRM path. AWS documents the Opus 4.6 and Sonnet 4.6 AU profiles and model capabilities.

The Render service now has `AWS_BEDROCK_FALLBACK_MODEL_ID=au.anthropic.claude-sonnet-4-6`. AI run provenance records provider, exact model, fallback source and fallback reason. Draft provenance records the AI run, provider/model, source message IDs and evidence summary.

The operator AI workspace now also implements: stale-draft detection when newer CRM activity exists; evidence visibility on drafts; a deterministic pre-send grounding check that blocks stale drafts, unresolved placeholders and unsupported inventory claims; explicit `Mark sent` outcome recording after WhatsApp is opened; and AI-run fallback visibility. Automatic WhatsApp sending remains disabled.

## 2026-10-01 — Final production verification

Render service easyfind-crm-d01-d05 (srv-darsv560tbcc73cu4ip0) is live from crm-ui-dashboard at commit 1c196577fc414be52c8fc889b3886f11e0e9da5d, deployment dep-dav82h3m8hqs7399j4ug. /health returns HTTP 200.
