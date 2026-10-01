## Current production audit — 2026-10-01

Verified live baseline is recorded in the authoritative current-state block below.

# Infrastructure Registry

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



This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- CRM UI production branch: `crm-ui-dashboard`
- CRM UI Render service: `easyfind-crm-d01-d05` (`https://easyfind-crm-d01-d05.onrender.com`)
- Local CRM UI checkout: `leads_automation/crm-ui-dashboard`
- Current CRM UI deployment is sourced from `crm-ui-dashboard`; the older SAM/main deployment notes below are historical infrastructure records and are not the CRM UI production path.

## CRM production checkpoint — 2026-09-30

- Render service: `easyfind-crm-d01-d05` (`srv-darsv560tbcc73cu4ip0`)
- Deployment branch: `crm-ui-dashboard`
- Latest live commit: 1c196577fc414be52c8fc889b3886f11e0e9da5d
- Live deployment: dep-dav82h3m8hqs7399j4ug
- Production source: `+919148338801`
- Supabase baseline: 186 leads, 310 classifications, 23 pending classifications, 6,870 messages, 465 webhook events (465 processed, 0 received, 0 processing, 0 failed).
- `main` is repository-reconciled to the same tree; Render remains on `crm-ui-dashboard`.

## Historical CRM prototype deployment target

## Historical CRM prototype deployment target

The existing dedicated Render service reserved for the future CRM prototype is:

| Property | Verified value |
|---|---|
| Service ID | `srv-dark8jm0tbcc73buokhg` |
| Service name | `leads-ui-dashboard` |
| URL | `https://leads-ui-dashboard.onrender.com` |
| Current repository | `zeidhussain9-cloud/easyfind-website` |
| Current branch | `feature/leads-automation` |
| Current root | `leads_automation/leads-ui` |
| Build | `npm install` |
| Start | `node simple-server.js` |
| Auto-deploy | enabled |

This service is **not repointed during reconciliation**. Repository/branch/root changes belong to the later prototype implementation/deployment step.

The Render environment variable names supplied for the future prototype are deployment configuration only. Secret values must never be recorded in Git.

## Established shared capabilities

- `shared/cloudinary/` — technical media storage/upload and stable media-reference helpers.
- `shared/google_sheets/` — technical Google Sheets connectivity and the canonical `Housing_Listings` schema/ownership contract.
- `shared/whatsapp_whapi/` — technical WhAPI authentication, transport, channel/settings primitives, webhook normalization, and neutral message primitives.
- `shared/google_maps/` — reusable Google Maps URL extraction and Geocoding resolution capability.
- `shared/slack/` — reusable Slack transport, security, routing, and Phase-1 operational capability.
- `shared/credentials/` — canonical local macOS Keychain credential provider for local development and local diagnostics.

## Credential provider map

| Shared capability | Canonical local Keychain service | Keychain account | Historical migration source |
|---|---|---|---|
| Cloudinary | `efps-whapi-panel-cloudinary` | `efps` | `efps-whapi-panel-cloudinary` |
| Google Sheets | `efps-whapi-panel-sheet` | `efps` | `efps-whapi-panel-sheet` |
| WhAPI | `efps-whapi-panel-token` | `efps` | `easyfind/whatsapp-api-credentials` |
| WhAPI webhook | `efps-whapi-panel-webhook` | `efps` | `easyfind/whatsapp-webhook-credentials` |
| Gemini/Vertex | `efps-whapi-panel-gemini` | `efps` | `easyfind/gemini-api-key` |
| Slack | `efps-whapi-panel-slack` | `efps` | `easyfind/slack-api-credentials` |
| Google Maps baseline migration service | `efps-whapi-panel-maps` | `efps` | `efps-whapi-panel-maps` |
| Google Maps current API credential | `efps-google-maps-api-key` | `efps` | dedicated Maps credential registry |

The Keychain entries are the local-development credential source. They are not a production Lambda credential mechanism. The SAM deployment contract uses existing AWS Secrets Manager secrets and injects only the required runtime environment variables; secret values are never stored in GitHub or this document. See `docs/DEPLOYMENT.md`.

## Google Sheets

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Immutable row identity: `listing_id` in column `A`
- Recorded service-account identity: `gcpnew@easyfind-automations.iam.gserviceaccount.com`
- Canonical local schema: `shared/google_sheets/schema.py`
- Physical grid: 48 columns, `A:AV`
- **Current reserved columns: `AU` (`source_group`) and `AV` (`inventory_locked`)**
- **Stage-1/2 recurring write boundary: `A:D` and `F:AO`**
- **Stage-3 downstream write boundary: `AP:AT` plus `C` for the catalogue lifecycle transition**
- **Initial row bootstrap:** the current Stage-1 runtime inserts a full 48-field row with `listing_state=Available`; subsequent Stage-1/2 updates protect E.
- AU/AV are reserved columns. Current runtime code must not populate them.
- A:AV rows may still be represented in memory to preserve the canonical 48-field schema, but AU/AV positions must remain blank.
- Stage-3 fields remain downstream-owned according to `shared/google_sheets/schema.py`; the reserved-column rule does not transfer ownership of AU/AV to any runtime stage.
- Historical live Sheet values in AU/AV require a separate controlled data-cleanup operation and are not changed by repository code.

## WhatsApp / WhAPI

- Canonical local Keychain service: `efps-whapi-panel-token`
- Keychain account: `efps`
- WhAPI base URL: `https://gate.whapi.cloud`
- Live-traffic approval flag: `EFPS_WHAPI_LIVE=1`
- Webhook token Keychain service: `efps-whapi-panel-webhook`
- Legacy webhook query parameter: `t`
- Retained inventory-listener sender numbers: `917975102130`, `919902024973`

Local runtime resolution can use the canonical Keychain service. Deployed Lambda resolution is defined separately in `template.yaml`: `WHAPI_API_TOKEN` is populated from the configured AWS Secrets Manager secret. The repository does not assert that the referenced production secret currently exists or contains a valid token; that requires AWS runtime verification.

### Previously verified live Inventory Phase-1 state

The connected WhAPI account was previously verified with read-only/live diagnostic requests:

- `GET /health`: HTTP 200.
- Connected display identity: `Easyfind Property Solutions`.
- Connected WhatsApp ID: `919148338801`.
- Business channel: `true`.
- Channel ID: `DRAXTH-J6HEU`.
- `GET /settings`: HTTP 200.
- A webhook was configured in `body` mode with `messages` / `POST` subscription.
- `GET /settings/events`: HTTP 200; `messages` / `post` was an allowed event.
- A direct synthetic JSON POST to the configured deployed webhook returned HTTP 200 with `{"ok": true, "queued": 1}`.
- The synthetic probe used non-inventory sender `919000000000`, so it could not open an Inventory Phase-1 property session.
- No WhAPI settings were modified and no customer message was sent during those acceptance checks.

These observations are historical runtime evidence, not proof that the current `main` commit is deployed or that current AWS credentials are valid. Current production state must be independently verified in AWS.

## Google Maps

- Google Cloud project: `easyfind-automations`
- Current API key display name: `Google Maps Key`
- Current key resource UID: `2334a827-466f-4a7a-8962-68c2afa29e34`
- Canonical local Keychain service: `efps-google-maps-api-key`
- Keychain account: `efps`
- Runtime variable accepted by the adapter: `GOOGLE_MAPS_API_KEY`
- Geocoding endpoint: `https://maps.googleapis.com/maps/api/geocode/json`
- API restriction: `geocoding-backend.googleapis.com`
- Runtime state: live direct API access, application-path resolution, and Inventory Stage-2 consumption were previously verified.
- Missing/incomplete Maps resolution fails closed into Inventory `Needs Review`; no location is guessed.

The current SAM deployment contract injects `GOOGLE_MAPS_API_KEY` from the configured AWS Secrets Manager secret. This does not prove that the AWS secret exists or that the deployed Lambda has been updated.

## Cloudinary

- Canonical local Keychain service: `efps-whapi-panel-cloudinary`
- Keychain account: `efps`
- Runtime variables accepted by the adapter: `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL`
- Optional explicit cloud name: `CLOUDINARY_CLOUD_NAME`
- Property public-ID convention: `properties/{listing_id}/photo_{n}`
- Lead public-ID namespace: `leads/{phone}/{message_id}_{n}`
- Catalogue helper limit: 10 URLs
- Runtime state: live Inventory Phase-1 upload acceptance was previously verified through the local application credential path.

The current SAM deployment contract injects `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` from the configured AWS Secrets Manager secret. This does not prove current AWS runtime connectivity.

## Slack

- Canonical local Keychain service: `efps-whapi-panel-slack`
- Keychain account: `efps`
- Runtime variables accepted by the adapter: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`
- Workspace/channel IDs are documented only where previously verified; current app installation, bot membership, command registration, and live endpoint behavior remain runtime verification items.
- Society approval commands, queues, cards, and workflows are explicitly excluded from the new architecture.

The current SAM deployment contract injects `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` from the configured AWS Secrets Manager secret. This does not prove that the Slack app is installed or that the current deployed endpoint is registered.

## Live-system runtime boundary — 2026-09-16

The repository-level migration uses the latest canonical `main` plus the approved live Stage-1 integration boundary. `modules/efps-inventory-mgmnt/src/inventory_runtime.py` requires the existing `efps-sessions` DynamoDB table and uses it only for durable Stage-1 session state. The SAM integration template requires `SessionsTableArn` for that table and grants the WhAPI webhook Lambda the minimum DynamoDB actions required for session lifecycle operations.

Lead resources and their stream remain externally supplied through the existing template parameters. The migration does not replace current Lead, Slack, WhAPI, Sheets, Maps, or Cloudinary implementations with older migration-branch versions.

## Credential policy

Only secret names/ARNs and non-sensitive identifiers may be documented here. Secret values, WhAPI tokens, Cloudinary API secrets, Google service-account private keys, webhook secrets, Slack signing secrets, and production credentials must remain outside version control.

The credential architecture is now explicitly split:

1. local development/diagnostics → macOS Keychain provider;
2. deployed Lambda runtime → existing AWS Secrets Manager secrets referenced by `template.yaml` dynamic references;
3. third-party runtime acceptance → independently verified AWS probes.

The migration itself does not prove live third-party connectivity. Each integration requires its own runtime acceptance probe.

## CRM dedicated deployment — verified 2026-09-27

The separate CRM UI deploys **only** from `crm-ui-dashboard` to Render service `easyfind-crm-d01-d05` (`srv-darsv560tbcc73cu4ip0`), URL `https://easyfind-crm-d01-d05.onrender.com`. It uses Supabase project `qttcutwzehtskfcwxkwj` through server-side TLS and hosted Ollama Cloud `gpt-oss:20b` through server-only `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_API_KEY`. A fictional hosted response was verified in Render logs at 2026-09-26 21:25:38 UTC. Root `steering.md` is bundled in the deployed repository and read server-side. No local model is installed. Repository `main` is a reconciled repository branch; Render production remains on `crm-ui-dashboard`.

## 2026-09-27 — Canonical branch transition

Repository reconciliation is maintained separately from the Render deployment path. `crm-ui-dashboard` is the Render branch; `main` is kept reconciled to the approved CRM repository checkpoint. The active CRM checkout is `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/crm-ui-dashboard`; the separate `main` worktree is `/Users/zeidzakir/Projects/efps-internal-automatios`.

## 2026-10-01 — CRM Render/AWS runtime checkpoint
Production CRM service srv-darsv560tbcc73cu4ip0 is on crm-ui-dashboard; the current deployment commit is recorded in the final checkpoint below. Bedrock region/model presence and database connectivity were verified at startup; AWS credentials are Render secrets.

## 2026-10-01 — AI runtime fallback

Render production Bedrock settings now include `AWS_BEDROCK_FALLBACK_MODEL_ID=au.anthropic.claude-sonnet-4-6`. Runtime order is Claude Opus 4.6 AU → Claude Sonnet 4.6 AU → Ollama `gpt-oss:20b`. AI run and draft provenance are persisted. AWS documents the Sonnet 4.6 AU geo inference profile as routing within Australia/New Zealand destinations. 

## Final verified checkpoint — 2026-10-01

Production Render service srv-darsv560tbcc73cu4ip0 is live on crm-ui-dashboard commit 1c196577fc414be52c8fc889b3886f11e0e9da5d. Health is HTTP 200. main tree equals 908b635b2b7b04bdf3515934de2769393e282c34.

## 2026-10-01 — Dependency security checkpoint

The AWS Bedrock runtime SDK was upgraded to `3.1144.0` after Render exposed a critical transitive `fast-xml-parser` advisory in the previous dependency tree. Local production-dependency audit now reports zero vulnerabilities; the historical automated suite was 71/71; current automated suite is 78/78 and browser regression is 1/1.
