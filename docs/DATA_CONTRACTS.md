# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

The inventory module is the business owner of canonical inventory meaning and inventory-specific decisions.

The shared Google Sheets layer owns the technical sheet-access mechanism and the canonical physical `Housing_Listings` contract used by this repository. The contract includes field names, physical order, ownership, writable permissions, row identity, allowed values where explicitly established, and derived ranges.

Canonical local source:

`shared/google_sheets/schema.py`

Verified legacy source:

`efps-platform/modules/efps-whapi-panel/src/schema.py`

Verified legacy machine-readable export:

`efps-platform/docs/SHEET_CONTRACT.json`

The verified legacy sheet is `Housing_Listings` in spreadsheet `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`, with row identity `listing_id` in column A. fileciteturn315file0L2-L2

## Housing_Listings ownership

The verified legacy contract assigns ownership as follows:

- `panel`: inventory fields plus raw/tail fields
- `housing_agent`: `posted_url`, `posted_at`, `error_notes`
- `meta_catalog`: `meta_catalog_id`, `meta_catalog_status`

The machine-readable contract is authoritative for the exact 48-column grid and writable field sets. fileciteturn322file0L2-L2 fileciteturn323file0L2-L2

A column owner or allowed-value rule is a business decision, not a refactor. Changes require an explicit owner decision and synchronized contract/document updates.

## Media contract

Cloudinary is a reusable technical capability. The owning module decides which media is stored and when. The verified legacy implementation uses deterministic listing-derived property paths and a separate lead/enquiry namespace. fileciteturn228file0L2-L2

## WhatsApp / WhAPI contract

WhAPI is a reusable technical integration capability. The shared layer owns authentication, transport, and verified endpoint primitives; business modules own workflow meaning. Live traffic must remain behind the explicit safety gate. fileciteturn223file0L2-L2

## Documentation impact rule

Changes to the `Housing_Listings` contract require review of:

- `shared/google_sheets/schema.py`
- `shared/google_sheets/README.md`
- module documentation for any module that reads/writes affected fields
- `docs/ARCHITECTURE.md`
- `docs/DATA_CONTRACTS.md`
- `docs/INFRASTRUCTURE.md` when infrastructure identifiers/configuration change
- `docs/OPEN_POINTERS.md` when a decision or unresolved fact is created/resolved
- all maintained root and `docs/` documents under the repository-wide full-review rule
