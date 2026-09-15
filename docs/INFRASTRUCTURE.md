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
- `shared/slack/` — reusable Slack transport, security, routing, and live operational capability.
- `shared/credentials/` — canonical local macOS Keychain credential provider.
- `shared/webhook/` — generic webhook request/response transport primitives.

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

Runtime credential resolution uses the following model: local development may use the canonical macOS Keychain provider; deployed AWS Lambdas use the environment variables populated by the `NoEcho` parameters in `template.yaml`. Secret values are never stored in GitHub or this document.

## Google Sheets

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Immutable row identity: `listing_id` in column `A`
- Recorded service-account identity: `gcpnew@easyfind-automations.iam.gserviceaccount.com`
- Canonical local schema: `shared/google_sheets/schema.py`
- Verified physical contract: 48 columns, `A:AV`
- Verified Stage-1/2 inventory write boundary: `A:D`, `F:AO`, `AU`
- Protected Stage-3 fields: `E`, `AP:AT`, `AV`

## WhatsApp / WhAPI

- Canonical Keychain service: `efps-whapi-panel-token`
- Keychain account: `efps`
- WhAPI base URL: `https://gate.whapi.cloud`
- Live-traffic approval flag: `EFPS_WHAPI_LIVE=1`
- Webhook token Keychain service: `efps-whapi-panel-webhook`
- Legacy webhook query parameter: `t`
- Retained inventory-listener sender numbers: `917975102130`, `919902024973`
- Canonical shared client sends `User-Agent: EFPS-Inventory-Phase1/1.0` on WhAPI API requests because that header was required by the previously verified Cloudflare-protected diagnostic path.

The legacy deployment uses one token/channel/connected-number relationship. The two numbers above are source-number configuration and are not proof of two WhAPI channels.

### Verified live Inventory Phase-1 state

The connected WhAPI account was previously verified with read-only/live diagnostic requests, including `GET /health`, settings/event discovery, and a non-inventory synthetic webhook POST. Those checks did not change WhAPI settings or send a customer message. This evidence applies to the previously deployed runtime; it does not by itself prove the destination migration runtime is live.

## Google Maps

- Google Cloud project: `easyfind-automations`
- Current API key display name: `Google Maps Key`
- Current key resource UID: `2334a827-466f-4a7a-8962-68c2afa29e34`
- Canonical Keychain service: `efps-google-maps-api-key`
- Keychain account: `efps`
- Runtime variable accepted by the adapter: `GOOGLE_MAPS_API_KEY`
- Geocoding endpoint: `https://maps.googleapis.com/maps/api/geocode/json`

## Cloudinary

- Canonical Keychain service: `efps-whapi-panel-cloudinary`
- Keychain account: `efps`
- Runtime variables accepted by the adapter: `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL`
- Optional explicit cloud name: `CLOUDINARY_CLOUD_NAME`
- Property public-ID convention: `properties/{listing_id}/photo_{n}`
- Lead public-ID namespace: `leads/{phone}/{message_id}_{n}`
- Catalogue helper limit: 10 URLs

## Slack

- Canonical Keychain service: `efps-whapi-panel-slack`
- Keychain account: `efps`
- Runtime variables accepted by the adapter: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`
- Workspace/channel IDs are documented only where previously verified; current app installation, bot membership, command registration, and live endpoint behavior remain runtime verification items.
- Slack inbound signatures are resolved from `SLACK_SIGNING_SECRET` in AWS and fall back to the local Keychain secret for local development.
- Slack Events `event_id` deduplication uses the existing `efps-sessions` table with an atomic conditional claim.

## Credential policy

Only secret names and non-sensitive identifiers may be documented here. Secret values, WhAPI tokens, Cloudinary API secrets, Google service-account private keys, webhook secrets, Slack signing secrets, and production credentials must remain outside version control.
