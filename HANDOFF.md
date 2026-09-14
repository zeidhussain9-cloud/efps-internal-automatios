# EFPS Internal Automations — Current Handoff

## Current state

The repository documentation foundation and mandatory AI steering layer are established. The shared layer has three capability boundaries: `cloudinary`, `google_sheets`, and `whatsapp_whapi`.

`CORE_STEERING.md` is mandatory for every AI agent, every interaction, and every iteration. `AGENTS.md` and `GEMINI.md` enforce it.

For every implementation, all maintained root documents and all documents in `docs/` must be reviewed against resulting repository reality. Affected documents must be updated in the same work session.

## Source review completed

The legacy `efps-platform` repository was reviewed for naming convention, business rules, document governance, architecture, infrastructure, the Google Sheets contract, WhAPI authentication, webhook configuration, webhook routing, inventory listeners, lead handling, and custom WhAPI skills.

The legacy WhAPI webhook uses a public Lambda Function URL, authenticates with a shared query parameter `?t=...`, acknowledges quickly, and can hand the payload to a separate asynchronous Lambda for slow processing. The webhook payload is normalized before routing. fileciteturn377file0L2-L2 fileciteturn379file0L2-L2

The legacy routing distinguishes direct messages from the two configured inventory-listener sender numbers from ordinary direct enquiries. Inventory-listener messages enter the inventory path; other direct messages enter the lead path. The legacy deployment configured those sender numbers as `917975102130` and `919902024973`. fileciteturn367file0L2-L2 fileciteturn380file0L2-L2

The legacy WhAPI skill documents webhook configuration through `PATCH /settings` with `webhooks[].url`, `mode: body`, and per-event `type`/`method` entries. fileciteturn384file0L2-L2

## Verified infrastructure references

- Google Sheets spreadsheet: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Google Sheets worksheet: `Housing_Listings`
- Google Sheets AWS secret: `efps-whapi-panel-sheet`
- WhAPI AWS secret: `efps-whapi-panel-token`
- WhAPI base URL: `https://gate.whapi.cloud`
- Cloudinary AWS secret: `efps-whapi-panel-cloudinary`
- WhAPI local token variable: `WHAPI_API_TOKEN`
- Google local credential variables: `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_APPLICATION_CREDENTIALS`
- Cloudinary local credential variables: `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL`

Actual credential values remain outside version control.

## Canonical Google Sheets contract

`shared/google_sheets/schema.py` is the local source for the `Housing_Listings` physical schema and ownership contract.

The verified machine-readable legacy contract is a 48-column grid ending at `AV`, with immutable `listing_id` as row identity. The older legacy `src/schema.py` table itself stopped at 47/AU; the newer generated `docs/SHEET_CONTRACT.json` contains the 48th `inventory_locked` column at AV. The new repository now explicitly models 48/A:AV and fails if it drifts.

## Shared capability implementation state

### `shared/cloudinary/`

Implemented as a reusable technical package boundary with dependency-injected upload transport, deterministic media support, and runtime credential contract.

### `shared/google_sheets/`

Implemented with credential loading, authenticated client creation, spreadsheet/worksheet access, range reads/writes, row append capability, and the corrected 48-column A:AV contract under `schema.py`. Production runtime wiring remains to be verified.

### `shared/whatsapp_whapi/`

Implemented with the verified token secret boundary, Bearer transport, live-traffic gate, canonical integration configuration, two inventory-listener sender numbers, webhook normalization, query-token verification, and legacy-compatible webhook registration payload construction. No live WhAPI settings are mutated by this repository automatically.

The legacy flow is now documented as: WhAPI channel -> public webhook Lambda URL -> token verification -> payload normalization -> inventory-listener routing or lead routing -> owning business module. Slow inventory work may be handed to an asynchronous Lambda so WhAPI receives a fast acknowledgement. fileciteturn377file0L2-L2 fileciteturn379file0L2-L2

### `modules/efpd-lead-mgmnt/`

Added immediately after `efps-inventory-mgmnt` in the repository module order. It is the future canonical owner of lead/enquiry business workflows. The shared WhAPI layer supplies transport/message data but does not own lead business decisions.

## Current AI skills

Repository-specific shared capability skills include:

- `.gemini/skills/cloudinary/`
- `.gemini/skills/google-sheets/`
- `.gemini/skills/whapi/`

## Current modules

- `efps-inventory-mgmnt`
- `efpd-lead-mgmnt`
- `efps-meta-catalogue-mgmnt`
- `efps-housing-portal-mgmnt`
- `efps-website-mgmnt`

## Next development rule

Before implementing a capability, apply `CORE_STEERING.md`, read the root guidance, `HANDOFF.md`, applicable `docs/`, and relevant module/shared guidance. Establish current source truth before changes. At the end of every implementation, review all maintained root and `docs/` documents, update every affected document, update `HANDOFF.md`, and validate the final repository state.
