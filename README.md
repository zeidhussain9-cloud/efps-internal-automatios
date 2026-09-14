# EFPS Internal Automations

Internal automation repository for EasyFind Property Solutions (EFPS).

The repository is organized into reusable technical integrations under `shared/` and business capabilities under `modules/`.

## Repository structure

- `shared/google_sheets/` — reusable Google Sheets integration capabilities.
- `shared/cloudinary/` — reusable Cloudinary image/media capabilities.
- `shared/whatsapp_whapi/` — reusable WhatsApp/WhAPI connection and API capabilities.
- `modules/efps-inventory-mgmnt/` — property inventory business workflows and rules.
- `modules/efps-meta-catalogue-mgmnt/` — Meta/WhatsApp catalogue business workflows.
- `modules/efps-housing-portal-mgmnt/` — placeholder for future Housing.com automation.
- `modules/efps-website-mgmnt/` — EasyFind website management and automation.
- `docs/` — cross-module architecture and shared data contracts.
- `.gemini/skills/` — repeatable AI session procedures.

This is the initial skeleton. Implementation is added only when the corresponding capability is actually required.