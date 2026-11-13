## Historical production audit — 2026-10-01

Verified live baseline is recorded in the authoritative current-state block below.

# Infrastructure Registry

## Current verified infrastructure update — 2026-11-13

- Isolated Notion stack `efps-notion-property-intake` in `ap-southeast-2`: `UPDATE_COMPLETE`.
- Notion Lambda `efps-notion-intake`: Active (Python 3.12; 512 MB; 180-second timeout). Updated via SAM on 2026-11-13; `LastUpdateStatus=Successful`, `$LATEST` CodeSha256 `+b4hBplC+2CGZag7HnpSDdmfwDqwuvHqtuSSLoGd/6c=`; CloudFormation stack `UPDATE_COMPLETE`.
- Notion endpoint: `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake`; invalid handshake/event signatures returned HTTP 401, a validly signed malformed event reached page validation (HTTP 400), and controlled create/archive probes for both Notion databases returned HTTP 200.
- Canonical editor: Notion Housing Listings. The repository now handles all eight Page event types and upserts/tombstones the existing `public.crm_inventory_snapshot` directly. The database allows `housing_notion`; Notion-owned IDs take precedence over Sheet compatibility sync.
- Supabase `notion-inventory-state` is ACTIVE v6 with JWT verification on, the direct projection, Listing ID allocation response, and a lookup that returns the deletion marker required for restore replay. Supabase currently confirms 104 active `housing_notion` rows (87 Available, 17 Rented Out), with no matching test rows or `housing_sheet` rows.
- Existing Slack/raw intake remains a compatibility producer. The dashboard queries active `housing_notion` rows only. Supabase cron `crm_inventory_sheet_reconcile_5m` was unscheduled; no five-minute Sheet reconciliation remains active.
- Existing WhAPI/CRM CloudFormation stack was not modified. Its EFPSWebhook Lambda is Active with EFPS_WHAPI_LIVE=1 and EFPS_WEBHOOK_LIVE=1; last function code update was 2026-10-04. The deployed artifact still contains the two old inventory sender routes (917975102130, 919902024973), but this is legacy inventory logic and is not the current intake workflow. It remains untouched until the final cleanup phase; this task did not redeploy the shared stack.
- The existing `EFPS CRM Property Intake` connection appears in Notion Developer Connections; the user confirms the webhook was already verified and all eight Page events remain selected. AWS identity is verified as account `294417174793` in `ap-southeast-2`. Existing secret ARNs were reused; no values were printed, copied, created, rotated, or overwritten. Direct mirror workers used the existing Notion credential at runtime.
- Live signed-in verification confirmed a Notion edit reached Supabase and the dashboard; a real Notion delete soft-deleted its row after about one minute. Restore was attempted through the Notion UI, but no Lambda invocation or Supabase Edge Function request followed and the projection remained soft-deleted. Direct worker restore passed separately; that does not verify webhook delivery. The exact test Supabase rows were removed and the test page was permanently deleted from Notion Trash after user approval.
- SAM rebuilt from the existing Linux dependency artifact because Docker is unavailable locally. Its package dependencies were checked and the source file hash matched the committed Lambda source. Generated SAM template validation passed; GitHub's SAM container build and dependency packaging check also passed on the release commit. Inventory Contract passed 130/130; repository audit, projection regression, Python compilation, local SAM lint, and browser check passed. Render release health smoke passed.

### Historical CRM production metrics checkpoint — 2026-10-05

The following CRM and inventory metrics are a dated historical snapshot, not current metrics for 2026-11-13. Re-run the live database/Render audit before treating them as current.

- **CRM deployment branch:** `crm-ui-dashboard`
- **Verified deterministic implementation baseline:** `8996dd32d732b0d8fab17f41b42306c230cd1de1`
- **CRM tree:** `c16bafdf7ed4e369d3171a4ee58f80a919630f10`
- **main:** reconciled release branch
- **main tree:** verified equal to crm-ui-dashboard at release close
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** current crm-ui-dashboard release = **LIVE**
- **Live Render:** current crm-ui-dashboard release verified LIVE
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 253 leads; 9,224 messages; 3,025 persisted WhAPI webhook events; 389 classifications; 253 normalized lead requirements; 277 AI runs; 214 drafts; 190 AI cursors; 88 inventory rows.
- **Classification status:** 253 promoted; 88 classified; 40 excluded; 8 pending = 389 total.
- **Webhook status:** 3,025 persisted webhook events; 0 failed processing records.
- **Message reconciliation:** 9,224 total CRM messages; current reconciliation evidence is maintained by the source-audit scheduler.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 696 stored distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 134/134 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v9.
- **AWS legacy webhook:** no changes in the audited CRM hardening range.
- **24-item CRM audit:** GREEN / VERIFIED.

### Historical operational flow snapshot

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
  -> event-driven Notion page updates (Sheets reconciliation disabled)
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
- Latest deterministic implementation baseline: 8996dd32d732b0d8fab17f41b42306c230cd1de1; current release is documented by the canonical verified-state file.
- Live deployment: current crm-ui-dashboard release verified LIVE in Render
- Production source: `+919148338801`
- Supabase baseline verified 2026-10-05: 253 leads, 389 classifications, 8 pending classifications, 9,224 messages, 3,025 persisted webhook events, 0 failed processing records.
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

## Notion Property Intake

- Intake database: `Property Intake — Raw Details & Photos` (`89dad7a3990849ca9dc23e5bcb3fa99f`)
- Housing Listings database: `bccfd4f55e294b269daa093a928f873a` (verified full-page database; data source `collection://416fedf9-b4e8-804e-8a49-000bf3a015ad`)
- Isolated SAM stack template: `notion-intake-template.yaml` (separate from the production WhAPI/CRM stack)
- SAM function: `efps-notion-intake`; API route: `/notion/intake`
- Idempotency: Supabase `public.crm_inventory_intake_events` via Edge Function `notion-inventory-state`; no DynamoDB dependency in this Notion stack.
- Runtime secret: AWS Secrets Manager `efps-notion-intake`, JSON keys `api_token` and `webhook_secret`
- Webhook authentication: Notion verification token captured during subscription handshake; subsequent `X-Notion-Signature` HMAC-SHA256 verification against the raw request body.
- Endpoint: `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake`.
- Historical raw Property Intake blocker: the previous acceptance pass recorded the AWS Sheets record as `{}` and Cloudinary/Maps as placeholders. This deployment turn did not re-read or change those values; raw Property Intake with photos may still be blocked. Direct Housing Listings-to-Supabase backfill completed using the existing Notion connection and direct projection path. Do not overwrite existing secret values as part of this workflow.
- This isolated stack does not update WhAPI/CRM Lambda functions, schedules, or the existing API Gateway.

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

Historical Stage-1/WhAPI runtime boundary: `modules/efps-inventory-mgmnt/src/inventory_runtime.py` retains the old `efps-sessions` DynamoDB session implementation. This is the legacy WhAPI inventory listener, not the Notion path, and is intentionally retained only until the final cleanup phase. The isolated Notion template has removed all DynamoDB references.

Lead resources and their stream remain externally supplied through the existing template parameters. The migration does not replace current Lead, Slack, WhAPI, Sheets, Maps, or Cloudinary implementations with older migration-branch versions.

## Credential policy

Only secret names/ARNs and non-sensitive identifiers may be documented here. Secret values, WhAPI tokens, Cloudinary API secrets, Google service-account private keys, webhook secrets, Slack signing secrets, and production credentials must remain outside version control.

The credential architecture is now explicitly split:

1. local development/diagnostics → macOS Keychain provider;
2. isolated Notion Lambda runtime → fetches existing AWS Secrets Manager values directly at runtime using secret ARNs (no plaintext credential environment variables and no CloudFormation dynamic references);
3. other deployed Lambda runtimes → their existing SAM/Secrets Manager contracts;
4. third-party runtime acceptance → independently verified API probes.

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

Production Render service srv-darsv560tbcc73cu4ip0 is live on crm-ui-dashboard commit 1982c7ea0a158ee0edcb00fad43e021876c13b9d (deploy dep-db1b2svf3r2c73brd6m0). Health is HTTP 200. Final main-tree equality is verified after the documentation release is reconciled into main.

## 2026-10-01 — Dependency security checkpoint

The AWS Bedrock runtime SDK was upgraded to `3.1144.0` after Render exposed a critical transitive `fast-xml-parser` advisory in the previous dependency tree. Local production-dependency audit now reports zero vulnerabilities; the historical automated suite was 71/71; current automated suite is 134/134 and browser regression is 1/1.
