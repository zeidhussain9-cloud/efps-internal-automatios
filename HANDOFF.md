# EFPS Internal Automations — Current Handoff

## Current state

The repository documentation foundation and mandatory AI steering layer are established. The shared layer has three capability boundaries: `cloudinary`, `google_sheets`, and `whatsapp_whapi`.

`CORE_STEERING.md` is mandatory for every AI agent, every interaction, and every iteration. `AGENTS.md` and `GEMINI.md` enforce it.

For every implementation, all maintained root documents and all documents in `docs/` must be reviewed against resulting repository reality. Affected documents must be updated in the same work session.

## Source review completed

The legacy `efps-platform` repository was reviewed for naming convention, business rules, document governance, architecture, infrastructure, the Google Sheets contract, WhAPI authentication, webhook configuration, webhook routing, inventory listeners, lead handling, and custom WhAPI skills.

The new repository intentionally does not copy legacy business workflow into `shared/`. Shared folders contain reusable technical capabilities; inventory and lead workflows remain module responsibilities.

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

Implemented as a reusable technical package boundary with AWS/local credential resolution, dependency-injected upload transport, deterministic property/lead public IDs, non-overwriting uploads, secure URL extraction, catalogue URL limiting, and media fingerprinting.

### `shared/google_sheets/`

Implemented with AWS/local credential loading, authenticated client creation, spreadsheet/worksheet access, range reads/writes, full-row read/write/append contract enforcement, canonical row mapping helpers, and the corrected 48-column A:AV schema/ownership contract.

### `shared/whatsapp_whapi/`

Implemented with AWS/local token resolution, Bearer transport, live-traffic gate, neutral `GET/POST/PATCH` transport, health/settings/event-discovery/webhook-test/text-message primitives, webhook normalization, constant-time query-token verification, retained sender-number configuration, and explicit-event webhook registration construction.

The shared WhAPI builder does not guess current event names or mutate live settings automatically. Current live channel identity, webhook URL, subscribed events, and deployed endpoint behavior remain runtime verification items.

## Production-readiness scope

The current hardening pass is limited to:

1. repository root governance documents;
2. all maintained `docs/` documents; and
3. everything under `shared/`.

Business modules are not being expanded as part of this scope.

Repository/source hardening is distinct from live external-system verification. GitHub source review cannot prove AWS credential access, Cloudinary account reachability, Google spreadsheet authorization, a currently connected WhatsApp number, or a deployed public webhook endpoint.

## Current modules

- `efps-inventory-mgmnt`
- `efpd-lead-mgmnt`
- `efps-meta-catalogue-mgmnt`
- `efps-housing-portal-mgmnt`
- `efps-website-mgmnt`

## Next development rule

Before implementing a capability, apply `CORE_STEERING.md`, read the root guidance, `HANDOFF.md`, applicable `docs/`, and relevant module/shared guidance. Establish current source truth before changes. At the end of every implementation, review all maintained root and `docs/` documents, update every affected document, update `HANDOFF.md`, and validate the final repository state.
