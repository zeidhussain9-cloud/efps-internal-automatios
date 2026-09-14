# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the new repository.

These are not instructions to guess or silently fix. An open pointer is a human-owned decision or a fact that still needs verification.

## Resolved references now verified from the legacy repository

- Google Sheets spreadsheet ID and `Housing_Listings` worksheet are verified.
- Google Sheets AWS secret name `efps-whapi-panel-sheet` and local credential variable names are verified.
- WhAPI AWS secret name `efps-whapi-panel-token`, local token variable, base URL, webhook token variable, and two inventory-listener sender numbers are verified from the legacy deployment/configuration.
- Cloudinary AWS secret name `efps-whapi-panel-cloudinary` is verified.
- The machine-readable legacy `Housing_Listings` contract is verified as a 48-column A:AV grid. The older legacy `src/schema.py` itself still contains the older 47-column/AU table; the generated `SHEET_CONTRACT.json` is the newer verified contract and is the source used to correct the new repository.

## Remaining pointers

- The actual secret values remain unavailable by design and must not be copied into GitHub.
- The exact live WhAPI channel/connected WhatsApp number and current deployed webhook URL cannot be verified from GitHub alone; they require an approved runtime/AWS/WhAPI check.
- The legacy deployment shows one WhAPI token/channel model. The two configured inventory numbers are sender/listener numbers used by the webhook to classify direct messages; they are not proven by the repository to be two separate WhAPI channels.
- The exact live webhook subscription state must be checked with the WhAPI channel settings before any live replacement/mutation. The legacy-compatible registration shape is preserved locally, but this repository does not silently mutate the live WhAPI account.
- Endpoint-specific WhAPI behavior must be verified from the current WhAPI API reference before adding live message/group/media operations beyond the transport and webhook normalization boundary.
- Exact production Cloudinary runtime access mechanism for the new repository must be verified before live uploads.
- Exact module integration points and business workflows remain to be established before wiring inventory and lead business logic into the shared capabilities.
- Website technical stack and deployment contract must be established before website automation is implemented.

## Current shared-capability truth

The repository has three established shared capability boundaries:

- `shared/cloudinary/`
- `shared/google_sheets/`
- `shared/whatsapp_whapi/`

Each has a repository-specific Gemini skill. Presence of a shared boundary does not imply that every runtime endpoint is complete or production-live.

When a pointer is resolved, update this document during the same work session and update the relevant architecture, business, contract, or infrastructure documentation.
