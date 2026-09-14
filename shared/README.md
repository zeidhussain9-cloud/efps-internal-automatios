# Shared Services

Reusable technical integrations used by multiple business modules.

## Boundary

Shared services provide technical capabilities only. They do not own inventory, lead, catalogue, portal, or website workflow decisions. Business modules decide **when**, **why**, and **for which business object** a shared capability is used.

## Folders

- `google_sheets/` — authenticated Sheets access plus the canonical `Housing_Listings` physical contract and ownership guards.
- `cloudinary/` — authenticated media upload, deterministic public IDs, stable secure URLs, and media fingerprints.
- `whatsapp_whapi/` — authenticated WhAPI transport, live-traffic gate, neutral channel/settings/message primitives, and webhook normalization/configuration helpers.

## Production boundary

The code in these folders is deployable as reusable technical components once the corresponding runtime credentials, external resources, and deployment endpoints are verified. A Git repository review alone does not prove live credentials, connected WhatsApp state, webhook reachability, or deployed AWS runtime state.

Secrets and private credentials are never stored in this folder or committed to Git.
