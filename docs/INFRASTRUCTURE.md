# Infrastructure Registry

This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- Default branch: `main`

## Established shared capabilities

- `shared/cloudinary/` — technical media storage/upload and stable media-reference helpers.
- `shared/google_sheets/` — technical Google Sheets connectivity and the canonical `Housing_Listings` schema/ownership contract.
- `shared/whatsapp_whapi/` — technical WhAPI authentication, transport, channel/settings primitives, webhook normalization, and neutral message primitives.
- `shared/google_maps/` — reusable Google Maps resolution capability.
- `shared/slack/` — reusable Slack transport, security, routing, and Phase-1 operational capability.

## Verified runtime credential map

| Shared capability | Verified AWS secret | Verified local/runtime name |
|---|---|---|
| Cloudinary | `efps-whapi-panel-cloudinary` | `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL` |
| Google Sheets | `efps-whapi-panel-sheet` | `GOOGLE_SERVICE_ACCOUNT_JSON` / `GOOGLE_APPLICATION_CREDENTIALS` |
| WhAPI | `efps-whapi-panel-token` | `WHAPI_API_TOKEN` |
| Google Maps | `efps-whapi-panel-maps` | `GOOGLE_MAPS_API_KEY` |
| Gemini/Vertex | `efps-whapi-panel-gemini` | `GEMINI_API_KEY`, `GOOGLE_API_KEY` / Vertex service-account environment |
| Slack | `efps-whapi-panel-slack` | `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` |

Only names are recorded here; secret values are runtime-only.

## Google Sheets

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Immutable row identity: `listing_id` in column `A`
- Recorded service-account identity: `gcpnew@easyfind-automations.iam.gserviceaccount.com`
- Canonical local schema: `shared/google_sheets/schema.py`
- Verified physical contract: 48 columns, `A:AV`
- Stage-1/2 inventory write boundary: `A:D`, `F:AO`, `AU`
- Protected Stage-3 fields: `E`, `AP:AT`, `AV`
- Housing Portal owns `AP:AR`; Meta Catalogue owns `AS:AT`; Panel owns `A:AO` and `AU:AV` physically, subject to the Stage-3 ownership boundary.

## WhatsApp / WhAPI

- AWS Secrets Manager secret: `efps-whapi-panel-token`
- Local token variable: `WHAPI_API_TOKEN`
- WhAPI base URL: `https://gate.whapi.cloud`
- Live-traffic approval flag: `EFPS_WHAPI_LIVE=1`
- Legacy webhook shared-token variable: `EFPS_WEBHOOK_TOKEN`
- Legacy webhook query parameter: `t`
- Retained inventory-listener sender numbers: `917975102130`, `919902024973`

The legacy deployment uses one token/channel/connected-number relationship. The two numbers above are source-number configuration and are not proof of two WhAPI channels.

Current WhAPI documentation confirms these relevant API surfaces: `GET /health`, `GET /settings`, `GET /settings/events`, `PATCH /settings`, `POST /settings/webhook_test`, and `POST /messages/text`. The shared client exposes neutral primitives for these operations. Live channel identity, webhook URL, subscription state, and endpoint behavior for the deployed account remain runtime verification items.

The shared webhook builder requires explicit event definitions discovered from `GET /settings/events`; it does not guess or silently reuse a legacy event list.

## Google Maps

- AWS secret: `efps-whapi-panel-maps`
- Runtime variable: `GOOGLE_MAPS_API_KEY`
- Live resolution is required before a supplied Maps URL can be treated as verified.
- Missing credentials or incomplete/partial resolution must fail closed into review; no location is guessed.

## Cloudinary

- AWS Secrets Manager secret: `efps-whapi-panel-cloudinary`
- Local/runtime variables: `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL`
- Optional explicit cloud name: `CLOUDINARY_CLOUD_NAME`
- Property public-ID convention: `properties/{listing_id}/photo_{n}`
- Lead public-ID namespace: `leads/{phone}/{message_id}_{n}`
- Catalogue helper limit: 10 URLs

Actual account access and a successful live upload remain runtime verification items.

## Slack

- AWS Secrets Manager secret: `efps-whapi-panel-slack`
- Runtime variables: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`
- Workspace/channel IDs are documented only where previously verified; current app installation, bot membership, command registration, and live endpoint behavior remain runtime verification items.
- Society approval commands, queues, cards, and workflows are explicitly excluded from the new architecture.

## Credential policy

Only secret names and non-sensitive identifiers may be documented here. Secret values, WhAPI tokens, Cloudinary API secrets, Google service-account private keys, webhook secrets, and production credentials must remain outside version control.
