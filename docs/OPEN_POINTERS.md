# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the new repository.

These are not instructions to guess or silently fix. An open pointer is a human-owned decision or a fact that still needs verification.

## Resolved references now verified from the legacy repository

- Google Sheets spreadsheet ID and `Housing_Listings` worksheet are verified.
- Google Sheets AWS secret name `efps-whapi-panel-sheet` is verified.
- WhAPI AWS secret name `efps-whapi-panel-token`, local token variable, and base URL are verified.
- Cloudinary AWS secret name `efps-whapi-panel-cloudinary` is verified.
- The legacy `Housing_Listings` schema and cross-project ownership contract are verified and have been established locally under `shared/google_sheets/schema.py`.

## Remaining pointers

- The actual secret values remain unavailable by design and must not be copied into GitHub.
- Exact production Cloudinary runtime access mechanism for the new repository must be verified before live uploads.
- Exact production WhAPI connection/account configuration must be verified before live endpoint operations beyond the safety-gated transport.
- Endpoint-specific WhAPI behavior must be verified from the current WhAPI API reference before implementing message/group/webhook operations.
- The local Google Sheets schema must remain fully synchronized with the verified 48-column legacy contract; the current local schema is intentionally fail-fast until all 48 fields are represented.
- Exact module integration points and business workflows remain to be established before wiring the shared capabilities into modules.
- Website technical stack and deployment contract must be established before website automation is implemented.

## Current shared-capability truth

The repository has three established shared capability boundaries:

- `shared/cloudinary/`
- `shared/google_sheets/`
- `shared/whatsapp_whapi/`

Each has a repository-specific Gemini skill. Presence of a shared boundary does not imply that every runtime endpoint is complete or production-live.

When a pointer is resolved, update this document during the same work session and update the relevant architecture, business, contract, or infrastructure documentation.
