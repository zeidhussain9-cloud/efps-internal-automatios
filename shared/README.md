# Shared Services

Reusable technical integrations used by multiple business modules.

## Boundary

Shared services provide technical capabilities only. They do not own inventory, lead, catalogue, portal, or website workflow decisions. Business modules decide **when**, **why**, and **for which business object** a shared capability is used.

## Folders

- `google_sheets/` — authenticated Sheets access plus the canonical `Housing_Listings` physical contract and ownership guards.
- `google_maps/` — Google Maps URL extraction and Geocoding resolution, including normalized `MapsResolution` results and fail-closed verification states.
- `credentials/` — canonical local macOS Keychain credential provider used by shared adapters.
- `cloudinary/` — authenticated media upload, deterministic public IDs, stable secure URLs, and media fingerprints.
- `whatsapp_whapi/` — authenticated WhAPI transport, live-traffic gate, neutral channel/settings/message primitives, and webhook normalization/configuration helpers.
- `slack/` — reusable Slack transport, security, routing, and authorized Inventory Phase-1 operational capability.

## Inventory Phase-1 verified boundaries

Google Sheets has a verified 48-column `Housing_Listings` contract and verified Stage-1/2 write boundary. Google Maps has verified live API access and verified consumption through the Inventory Stage-2 application path. These shared services remain technical capabilities; Inventory Management owns business decisions about when and why they are invoked.

## Production boundary

A shared implementation being present does not prove every runtime capability is live. Corresponding runtime credentials, external resources, and deployment endpoints must be verified separately. Current remaining runtime acceptance items are documented in `docs/OPEN_POINTERS.md`.

Secrets and private credentials are never stored in this folder or committed to Git.
