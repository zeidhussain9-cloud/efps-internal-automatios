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

## Verified dropdown/value contract

Live read-only inspection of the production worksheet established the following:

| Column | Field | Exact observed validation/value contract |
|---|---|---|
| D | `internal_property_type` | strict `ONE_OF_LIST`: `Gated Community`, `Semi Gated`, `Standalone` |
| M | `furnish_type` | strict `ONE_OF_LIST`: `Fully Furnished`, `Semi Furnished` |
| Y | `preferred_tenant_type` | strict `ONE_OF_LIST`: `Family`, `Open For All` |
| Z | `bachelor_preference` | strict `ONE_OF_LIST`: `Female Only `, `Male Only`, `Open for both` |
| AA | `pet_friendly` | no Sheet data-validation rule; populated values observed: `Yes`, `No` |
| AE | `society_amenities` | strict `ONE_OF_LIST`: `Security, Lift, CCTV, Power Backup`; `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `-` |
| AF | `flat_furnishings` | strict `ONE_OF_LIST`: `Wardrobe, Modular Kitchen, Geyser, Fan, Light`; `Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table` |

The live `Female Only ` validation value contains a trailing space; the exact observation is retained in the contract documentation rather than silently altered.

No conditional/row-dependent dropdown validation was observed for D, M, Y, Z, AE, or AF in the inspected range. Dependencies between these fields are therefore implemented as application/business rules rather than Google Sheets conditional dropdown rules.

## Furnish-type reconciliation

The live Sheet does not allow `Unfurnished` as a `furnish_type` value. The repository contract is aligned accordingly. Source text indicating an unfurnished property leaves `furnish_type` and `flat_furnishings` blank rather than introducing a third Sheet value.

## Business dependencies represented by the canonical schema

- `society_amenities` depends on `internal_property_type`.
- `flat_furnishings` depends on `furnish_type`.
- `bachelor_preference` depends on `preferred_tenant_type`.
- `maintenance` depends on `maintenance_included`.
- `security_deposit` depends on `monthly_rent`.

The current deterministic implementation supplies the exact canonical amenity and furnishing bundles only when the target field is blank. `Family` clears `bachelor_preference`; `Open For All` defaults to the exact live value `Open for both`, while explicit valid `Female Only ` or `Male Only` source evidence overrides that default. These rules are application/business contracts rather than Sheet conditional-dropdown rules.

## Ownership and downstream boundary

- Inventory/panel owns the Stage-1/2 fields. AU (`source_group`) and AV (`inventory_locked`) are reserved and must remain blank.
- Housing Portal owns AP:AR: `posted_url`, `posted_at`, `error_notes`.
- Meta Catalogue owns AS:AT: `meta_catalog_id`, `meta_catalog_status`.
- Lifecycle/control owns E and AV: `listing_state`, `inventory_locked`.

Inventory Stage-1/2 writes are explicitly restricted to A:D and F:AO. E, AP:AT, AU, and AV are protected/reserved.

## Canonical schema

`schema.py` is the single maintained source of truth for:

- physical column order and letters
- field names
- owner of every column
- top-level population stage
- writable permissions
- verified allowed values
- declared dependencies
- row identity
- derived ranges
- row-width and ownership integrity checks

## Verified Phase-1 runtime state

The canonical spreadsheet connection has been live-read successfully and the production write boundary has been verified without performing an unauthorized production write. The verified Stage-1/2 write ranges are:

- `A:D`
- `F:AO`
- `AU` (reserved; must remain blank)

The protected Stage-3 ranges are `E`, `AP:AT`, and `AV`.

The verified production worksheet contains the expected 48-column `Housing_Listings` contract. This establishes the current runtime authorization and contract boundary for Inventory Phase 1; it does not authorize Stage-3 writers.

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
