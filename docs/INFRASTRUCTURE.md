# Infrastructure Registry

This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- Default branch: `main`

## Established shared capabilities

- `shared/cloudinary/` — technical media storage/upload and stable media-reference operations.
- `shared/google_sheets/` — technical Google Sheets connectivity and the canonical `Housing_Listings` schema/ownership contract.
- `shared/whatsapp_whapi/` — technical WhAPI connectivity, authentication, webhook, messaging/media, and connection operations.

## Verified legacy infrastructure references

### Google Sheets

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- AWS Secrets Manager secret name: `efps-whapi-panel-sheet`
- Local-development credential variables: `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_APPLICATION_CREDENTIALS`
- Recorded service-account identity: `gcpnew@easyfind-automations.iam.gserviceaccount.com`

These identifiers are taken from the verified legacy implementation. fileciteturn315file0L2-L2 fileciteturn328file0L2-L2

### WhatsApp / WhAPI

- AWS Secrets Manager secret name: `efps-whapi-panel-token`
- Local-development token variable: `WHAPI_API_TOKEN`
- WhAPI base URL: `https://gate.whapi.cloud`
- Live-traffic approval flag: `EFPS_WHAPI_LIVE=1`

These are verified from the legacy implementation and guard. fileciteturn315file0L2-L2 fileciteturn316file0L2-L2 fileciteturn223file0L2-L2

### Cloudinary

- Legacy AWS Secrets Manager secret name: `efps-whapi-panel-cloudinary`
- Runtime credential fields supported by the legacy implementation: Cloudinary cloud name, API key, API secret, or a `CLOUDINARY_URL` representation.
- New shared runtime variable names: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

The legacy code confirms the secret name and credential-loading contract via its `SECRET_NAMES` and `cloudinary_creds()` implementation. fileciteturn315file0L2-L2 fileciteturn328file0L2-L2

## Credential policy

Only secret names and non-sensitive identifiers may be documented here. Secret values, WhAPI tokens, Cloudinary API secrets, Google service-account private keys, webhook secrets, and production credentials must remain outside version control.
