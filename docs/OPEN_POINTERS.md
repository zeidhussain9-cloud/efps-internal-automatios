# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the new repository.

These are not instructions to guess or silently fix. An open pointer is a human-owned decision or a fact that still needs verification.

## Resolved references now verified from the legacy repository

- Google Sheets spreadsheet ID and `Housing_Listings` worksheet are verified.
- Google Sheets AWS secret name `efps-whapi-panel-sheet` and local credential variable names are verified.
- WhAPI AWS secret name `efps-whapi-panel-token`, local token variable, base URL, webhook token variable, and two inventory-listener sender numbers are verified from the legacy deployment/configuration.
- The repository now contains the two-listener source boundary: exactly the two dedicated inventory sender numbers use the inventory listener; other inbound traffic uses the lead listener path, while groups/promotions remain outside the inventory listener boundary.
- Cloudinary AWS secret name `efps-whapi-panel-cloudinary` is verified.
- The machine-readable legacy `Housing_Listings` contract is verified as a 48-column A:AV grid. The older legacy `src/schema.py` itself still contains the older 47-column/AU table; the generated `SHEET_CONTRACT.json` is the newer verified contract and is the source used to correct the new repository.
- The current WhAPI public documentation confirms `GET /health`, `GET /settings`, `GET /settings/events`, `PATCH /settings`, `POST /settings/webhook_test`, and `POST /messages/text` as current API surfaces used by the shared connection boundary.

## Remaining pointers

- The actual secret values remain unavailable by design and must not be copied into GitHub.
- The exact live WhAPI channel/connected WhatsApp number and current deployed webhook URL cannot be verified from GitHub alone; they require an approved runtime/AWS/WhAPI check.
- The legacy deployment shows one WhAPI token/channel model. The two configured inventory numbers are sender/listener numbers used by the webhook to classify direct messages; they are not proven by the repository to be two separate WhAPI channels.
- The exact live webhook subscription state must be read from `GET /settings` and the currently allowed event list from `GET /settings/events` before any live replacement/mutation.
- A live webhook test must be performed against the deployed HTTPS endpoint before production traffic is enabled.
- The current shared webhook builder deliberately requires explicit event definitions discovered from WhAPI rather than hardcoding a legacy event list.
- Exact production Cloudinary runtime access mechanism and a successful live upload remain runtime verification items.
- Exact production Google Sheets access, service-account authorization to the spreadsheet, and a safe read/write smoke test remain runtime verification items.
- Exact module integration points and business workflows remain to be established before wiring inventory and lead business logic into the shared capabilities.
- Website technical stack and deployment contract must be established before website automation is implemented.

## Current shared-capability truth

The repository has three established shared capability boundaries:

- `shared/cloudinary/`
- `shared/google_sheets/`
- `shared/whatsapp_whapi/`

These are technical connection/storage primitives. They do not contain the inventory or lead workflow. Presence of a shared boundary does not imply that every external runtime has been authenticated or verified.

When a pointer is resolved, update this document during the same work session and update the relevant architecture, business, contract, or infrastructure documentation.
