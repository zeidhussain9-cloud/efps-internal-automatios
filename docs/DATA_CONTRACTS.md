# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

The inventory module is the business owner of canonical inventory meaning and inventory-specific decisions.

The shared Google Sheets layer owns the technical sheet-access mechanism and the canonical physical `Housing_Listings` contract used by this repository. The local contract is **48 physical columns, A:AV** and includes field names, physical order, ownership, writable permissions, row identity, explicitly established allowed values, and derived ranges.

Canonical local source:

`shared/google_sheets/schema.py`

Verified legacy sources:

- `efps-platform/modules/efps-whapi-panel/src/schema.py` — older 47-column table.
- `efps-platform/docs/SHEET_CONTRACT.json` — newer verified 48-column A:AV machine-readable contract.

The correction in this repository follows the newer generated contract, including `inventory_locked` at AV.

The verified legacy sheet is `Housing_Listings` in spreadsheet `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`, with row identity `listing_id` in column A.

## Housing_Listings ownership

The verified contract assigns ownership as follows:

- `panel`: A–AJ plus AP–AV
- `housing_agent`: AK–AM (`posted_url`, `posted_at`, `error_notes`)
- `meta_catalog`: AN–AO (`meta_catalog_id`, `meta_catalog_status`)

Rows are addressed by immutable `listing_id`, never by row position.

A column owner or allowed-value rule is a business decision, not a refactor. Changes require an explicit owner decision and synchronized contract/document updates.

## Media contract

Cloudinary is a reusable technical capability. The owning module decides which media is stored and when. The verified legacy implementation uses deterministic listing-derived property paths and a separate lead/enquiry namespace.

## WhatsApp / WhAPI contract

WhAPI is a reusable technical integration capability. The shared layer owns authentication, transport, webhook configuration/normalization, and integration metadata. The inventory and lead modules own the meaning and business processing of messages. The verified legacy inventory-listener numbers are `917975102130` and `919902024973`; they are source-number routing facts, not proven separate WhAPI channels.

## Documentation impact rule

Changes to the `Housing_Listings` contract require review of:

- `shared/google_sheets/schema.py`
- `shared/google_sheets/README.md`
- module documentation for any module that reads/writes affected fields
- `docs/ARCHITECTURE.md`
- `docs/DATA_CONTRACTS.md`
- `docs/INFRASTRUCTURE.md` when infrastructure identifiers/configuration change
- `docs/OPEN_POINTERS.md` when a decision or unresolved fact is created/resolved
- `HANDOFF.md`
- all maintained root and `docs/` documents under the repository-wide full-review rule
