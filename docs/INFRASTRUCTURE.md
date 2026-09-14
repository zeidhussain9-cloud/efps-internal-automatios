# Infrastructure Registry

This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- Default branch: `main`

## Established shared capabilities

- `shared/cloudinary/` — technical media storage/upload and stable media-reference operations.
- `shared/google_sheets/` — technical Google Sheets connectivity and the canonical `Housing_Listings` schema/ownership contract.
- `shared/whatsapp_whapi/` — technical WhAPI connectivity, authentication, webhook, messaging/media, and connection operations.

## Verified runtime credential map

| Shared capability | Verified AWS secret | Verified local/runtime name |
|---|---|---|
| Cloudinary | `efps-whapi-panel-cloudinary` | `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL` |
| Google Sheets | `efps-whapi-panel-sheet` | `GOOGLE_SERVICE_ACCOUNT_JSON` / `GOOGLE_APPLICATION_CREDENTIALS` |
| WhAPI | `efps-whapi-panel-token` | `WHAPI_API_TOKEN` |

Only names are recorded here; secret values are runtime-only.

## Google Sheets

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Immutable row identity: `listing_id` in column `A`
- Recorded service-account identity: `gcpnew@easyfind-automations.iam.gserviceaccount.com`
- Canonical local schema: `shared/google_sheets/schema.py`
- Verified physical contract: 48 columns, `A:AV`

## WhatsApp / WhAPI

- AWS Secrets Manager secret: `efps-whapi-panel-token`
- Local token variable: `WHAPI_API_TOKEN`
- WhAPI base URL: `https://gate.whapi.cloud`
- Live-traffic approval flag: `EFPS_WHAPI_LIVE=1`
- Webhook shared-token variable: `EFPS_WEBHOOK_TOKEN`
- Webhook query parameter: `t`
- Inventory-listener sender numbers: `917975102130`, `919902024973`

The legacy deployment uses one channel/token model; the two numbers above are the configured source numbers used by the webhook to identify inventory messages. The exact currently connected WhatsApp channel and live webhook URL still require runtime verification.

The legacy webhook registration shape is `PATCH /settings` with `webhooks[].url`, `mode: body`, and per-event `type`/`method` entries. The shared repository can construct this payload but does not silently mutate live WhAPI settings.

## Cloudinary

- AWS Secrets Manager secret: `efps-whapi-panel-cloudinary`
- Local/runtime variables: `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL`
- The new shared client may also accept `CLOUDINARY_CLOUD_NAME` as an explicit runtime field when the deployment supplies it.

## Credential policy

Only secret names and non-sensitive identifiers may be documented here. Secret values, WhAPI tokens, Cloudinary API secrets, Google service-account private keys, webhook secrets, and production credentials must remain outside version control.
