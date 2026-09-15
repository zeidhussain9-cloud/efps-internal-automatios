# Infrastructure Registry

This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- Default branch: `main`

## Established shared capabilities

- `shared/cloudinary/` — technical media storage/upload and stable media-reference helpers.
- `shared/google_sheets/` — technical Google Sheets connectivity and the canonical `Housing_Listings` schema/ownership contract.
- `shared/whatsapp_whapi/` — technical WhAPI authentication, transport, channel/settings primitives, webhook normalization, and neutral message primitives.
- `shared/google_maps/` — reusable Google Maps URL extraction and Geocoding resolution capability.
- `shared/slack/` — reusable Slack transport, security, routing, and Phase-1 operational capability.
- `shared/credentials/` — canonical local macOS Keychain credential provider.

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

The AWS entries identify historical migration sources only. Runtime resolution in the current repository uses the local Keychain provider. Secret values are never stored in GitHub or this document.

## Google Sheets

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Immutable row identity: `listing_id` in column `A`
- Recorded service-account identity: `gcpnew@easyfind-automations.iam.gserviceaccount.com`
- Canonical local schema: `shared/google_sheets/schema.py`
- Verified physical contract: 48 columns, `A:AV`
- Verified Stage-1/2 inventory write boundary: `A:D`, `F:AO`, `AU`
- Protected Stage-3 fields: `E`, `AP:AT`, `AV`
- Housing Portal owns `AP:AR`; Meta Catalogue owns `AS:AT`; Panel owns `A:AO` and `AU:AV` physically, subject to the Stage-3 ownership boundary.
- Runtime state: canonical read and write-boundary verification completed for Inventory Phase 1.

## WhatsApp / WhAPI

- Canonical Keychain service: `efps-whapi-panel-token`
- Keychain account: `efps`
- WhAPI base URL: `https://gate.whapi.cloud`
- Live-traffic approval flag: `EFPS_WHAPI_LIVE=1`
- Webhook token Keychain service: `efps-whapi-panel-webhook`
- Legacy webhook query parameter: `t`
- Retained inventory-listener sender numbers: `917975102130`, `919902024973`

The current runtime credential provider reads the canonical Keychain service and does not require AWS Secrets Manager access. The legacy deployment uses one token/channel/connected-number relationship. The two numbers above are source-number configuration and are not proof of two WhAPI channels.

Current WhAPI documentation confirms these relevant API surfaces: `GET /health`, `GET /settings`, `GET /settings/events`, `PATCH /settings`, `POST /settings/webhook_test`, and `POST /messages/text`. The shared client exposes neutral primitives for these operations. Live channel identity, webhook URL, subscription state, and endpoint behavior for the deployed account remain runtime verification items.

The shared webhook builder requires explicit event definitions discovered from `GET /settings/events`; it does not guess or silently reuse a legacy event list.

## Google Maps

- Google Cloud project: `easyfind-automations`
- Current API key display name: `Google Maps Key`
- Current key resource UID: `2334a827-466f-4a7a-8962-68c2afa29e34`
- Canonical Keychain service: `efps-google-maps-api-key`
- Keychain account: `efps`
- Runtime variable accepted by the adapter: `GOOGLE_MAPS_API_KEY`
- Geocoding endpoint: `https://maps.googleapis.com/maps/api/geocode/json`
- API restriction: `geocoding-backend.googleapis.com`
- Runtime state: live direct API access, application-path resolution, and Inventory Stage-2 consumption verified.
- Verified Maps URL resolution returned `VERIFIED` confidence and structured locality/pincode/coordinates for the test location.
- Missing/incomplete Maps resolution fails closed into Inventory `Needs Review`; no location is guessed.

The separate existing `Maps Platform API Key` resource remains documented in `shared/google_maps/CREDENTIALS.md` with its secret-storage mapping marked `NOT VERIFIED`.

## Cloudinary

- Canonical Keychain service: `efps-whapi-panel-cloudinary`
- Keychain account: `efps`
- Runtime variables accepted by the adapter: `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL`
- Optional explicit cloud name: `CLOUDINARY_CLOUD_NAME`
- Property public-ID convention: `properties/{listing_id}/photo_{n}`
- Lead public-ID namespace: `leads/{phone}/{message_id}_{n}`
- Catalogue helper limit: 10 URLs

Actual account access and a successful live upload remain runtime verification items.

## Slack

- Canonical Keychain service: `efps-whapi-panel-slack`
- Keychain account: `efps`
- Runtime variables accepted by the adapter: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`
- Workspace/channel IDs are documented only where previously verified; current app installation, bot membership, command registration, and live endpoint behavior remain runtime verification items.
- Society approval commands, queues, cards, and workflows are explicitly excluded from the new architecture.

## Credential policy

Only secret names and non-sensitive identifiers may be documented here. Secret values, WhAPI tokens, Cloudinary API secrets, Google service-account private keys, webhook secrets, Slack signing secrets, and production credentials must remain outside version control.

The credential migration pattern is: historical AWS source values → local macOS Keychain services under account `efps` → shared adapters. The migration itself does not prove live third-party connectivity; each integration requires its own runtime acceptance probe.
