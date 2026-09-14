# Infrastructure Registry

This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- Default branch: `main`

## Established shared capabilities

- `shared/cloudinary/` — technical media storage/upload and stable media-reference operations.
- `shared/google_sheets/` — technical Google Sheets connectivity and worksheet/range operations.
- `shared/whatsapp_whapi/` — technical WhAPI connectivity, authentication, webhook, messaging/media, and connection operations.

## Credential policy

The legacy implementation establishes a pattern of resolving runtime credentials from a managed secret store with environment-variable fallback for local development. fileciteturn229file0L2-L2

This repository must never contain secret values. At most, it may document approved secret names or environment-variable names.

Expected Cloudinary configuration names for the current shared implementation are:

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

The actual values must be supplied only at runtime through the approved secret/configuration mechanism.

WhAPI live network operations additionally require an explicit runtime approval gate, following the verified legacy guard pattern. fileciteturn223file0L2-L2

Google Sheets credentials likewise remain runtime-only; service-account private keys must never be committed.
