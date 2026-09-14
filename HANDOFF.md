# EFPS Internal Automations — Current Handoff

## Current state

The repository documentation foundation and mandatory AI steering layer are established. The shared layer now has three established capability boundaries: `cloudinary`, `google_sheets`, and `whatsapp_whapi`.

`CORE_STEERING.md` is mandatory for every AI agent, every interaction, and every iteration. `AGENTS.md` and `GEMINI.md` enforce it.

For every implementation, all maintained root documents and all documents in `docs/` must be reviewed against resulting repository reality. Affected documents must be updated in the same work session.

## Source review completed

The legacy `efps-platform` repository was reviewed for naming convention, business rules, document governance, architecture, infrastructure registry, cross-project contract, open-pointer practices, and custom agent skills.

The legacy `efps-whapi-panel` provides verified reference behavior for the shared capability boundaries. Its Cloudinary media layer uses deterministic property paths and a separate lead-media namespace. Its configuration resolves credentials from AWS Secrets Manager with environment-variable fallback. Its WhAPI network traffic is explicitly gated before live calls. fileciteturn228file0L2-L2 fileciteturn229file0L2-L2 fileciteturn223file0L2-L2

## Verified infrastructure references

- Google Sheets spreadsheet: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Google Sheets worksheet: `Housing_Listings`
- Google Sheets AWS secret: `efps-whapi-panel-sheet`
- WhAPI AWS secret: `efps-whapi-panel-token`
- WhAPI base URL: `https://gate.whapi.cloud`
- Cloudinary AWS secret: `efps-whapi-panel-cloudinary`

Actual credential values remain outside version control.

## Canonical Google Sheets contract

`shared/google_sheets/schema.py` is the local source for the `Housing_Listings` physical schema and ownership contract. It is derived from the verified legacy `modules/efps-whapi-panel/src/schema.py` and `docs/SHEET_CONTRACT.json`.

The verified legacy contract is a 48-column grid ending at `AV`, with immutable `listing_id` as row identity. The local representation is currently fail-fast until every one of the 48 fields is represented exactly; it must not silently use the older 47-column shape.

## Shared capability implementation state

### `shared/cloudinary/`

Implemented as a reusable technical package boundary with credential loading, dependency-injected upload transport, deterministic property and lead media identifiers, upload helpers, catalogue URL limiting, and image fingerprinting. Live credentials are not stored in the repository.

### `shared/google_sheets/`

Restored and implemented with credential loading, authenticated client creation, spreadsheet/worksheet access, range reads/writes, row append capability, and the canonical sheet contract under `schema.py`. Exact production runtime wiring remains to be verified.

### `shared/whatsapp_whapi/`

Restored and implemented with credential loading, Bearer authentication, configurable base URL, GET/POST transport, and an explicit `EFPS_WHAPI_LIVE=1` safety gate. Endpoint-specific messaging, group, media, webhook, and health operations must be implemented only from verified current WhAPI API references.

## Current AI skills

Repository-specific shared capability skills now include:

- `.gemini/skills/cloudinary/`
- `.gemini/skills/google-sheets/`
- `.gemini/skills/whapi/`

## Current modules

- `efps-inventory-mgmnt`
- `efps-meta-catalogue-mgmnt`
- `efps-housing-portal-mgmnt`
- `efps-website-mgmnt`

## Next development rule

Before implementing a capability, apply `CORE_STEERING.md`, read the root guidance, `HANDOFF.md`, applicable `docs/`, and relevant module/shared guidance. Establish current source truth before changes. At the end of every implementation, review all maintained root and `docs/` documents, update every affected document, update `HANDOFF.md`, and validate the final repository state.
