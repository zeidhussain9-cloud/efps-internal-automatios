# Google Sheets Shared Service

Provides the reusable technical capability for connecting to and operating Google Sheets.

## Responsibility

This shared layer owns technical access and the physical contract only:

- Google service-account credential loading
- authenticated Sheets client creation
- spreadsheet and worksheet access
- arbitrary range reads/writes
- canonical full-row reads/writes/appends for `Housing_Listings`
- canonical row-to-mapping and mapping-to-row conversion
- contract-width validation
- ownership guards exposed by `schema.py`
- connection/error handling suitable for calling modules

Business meaning and workflow decisions remain with the owning module. Shared Sheets code does not decide inventory or lead workflow.

## Credential resolution

| Item | Current value |
|---|---|
| Keychain service | `efps-whapi-panel-sheet` |
| Keychain account | `efps` |
| Historical migration source | `efps-whapi-panel-sheet` |
| Environment fallbacks | `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_APPLICATION_CREDENTIALS` |

The current repository resolves the canonical local macOS Keychain service after environment fallbacks. The private key/JSON value is never stored in GitHub.

## Canonical EFPS inventory sheet

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Immutable row identity: `listing_id` in column `A`
- Physical contract: **48 columns, A:AV**
- Physical order: maintained exclusively in `schema.py` and locked by tests to the latest supplied order.

## Ownership and downstream boundary

- Inventory/panel owns the Stage-1/2 fields and `source_group` at AU.
- Housing Portal owns AP:AR: `posted_url`, `posted_at`, `error_notes`.
- Meta Catalogue owns AS:AT: `meta_catalog_id`, `meta_catalog_status`.
- Lifecycle/control owns E and AV: `listing_state`, `inventory_locked`.

Inventory Stage-1/2 writes are explicitly restricted to A:D, F:AO, and AU so lifecycle/downstream state cannot be erased by a late processing update.

## Canonical schema

`schema.py` is the single maintained source of truth for:

- physical column order and letters
- field names
- owner of every column
- top-level population stage
- writable permissions
- explicitly verified allowed values
- row identity
- derived ranges
- row-width and ownership integrity checks

Exact sheet dropdown vocabularies that are not verified in repository source are intentionally left unclaimed rather than guessed.

## Verified Phase-1 runtime state

The canonical spreadsheet connection has been live-read successfully and the production write boundary has been verified without performing an unauthorized production write. The verified Stage-1/2 write ranges are:

- `A:D`
- `F:AO`
- `AU`

The protected Stage-3 ranges are `E`, `AP:AT`, and `AV`.

The verified production worksheet contains the expected 48-column `Housing_Listings` contract. This establishes the current runtime authorization and contract boundary for Inventory Phase 1; it does not authorize Stage-3 writers or invent unverified sheet control vocabularies.

## Documentation impact for contract changes

Any change to the physical sheet contract must update, in the same implementation session:

1. `shared/google_sheets/schema.py`
2. `shared/google_sheets/README.md`
3. `docs/DATA_CONTRACTS.md`
4. `docs/ARCHITECTURE.md` when ownership/boundary changes
5. `docs/INFRASTRUCTURE.md` when spreadsheet/runtime configuration changes
6. `docs/OPEN_POINTERS.md` when anything remains unverified
7. `HANDOFF.md`
8. All maintained root/`docs/` files under the repository-wide documentation rule.

No second schema may be created in a module.
