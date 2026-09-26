# Infrastructure Registry

This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- Default branch: `main`
- Repository code and production deployment contract are maintained on `main`. CRM reconciliation and prototype work uses isolated branches and does not modify `main`.

## CRM prototype deployment target

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
