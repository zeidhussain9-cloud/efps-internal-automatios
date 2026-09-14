# Google Sheets Shared Service

Provides the reusable technical capability for connecting to and operating Google Sheets.

## Responsibility

This shared layer owns technical access only:

- Google service-account credential loading
- authenticated Sheets client creation
- spreadsheet and worksheet access
- range reads
- range writes
- row appends when explicitly requested by the caller
- connection/error handling suitable for calling modules

Business meaning and workflow decisions remain with the owning module. The canonical physical sheet contract is centralized here so modules cannot silently redefine columns or ownership.

## Verified AWS/runtime credential map

| Shared capability | Verified AWS secret | Verified local/runtime name |
|---|---|---|
| Google Sheets | `efps-whapi-panel-sheet` | `GOOGLE_SERVICE_ACCOUNT_JSON` / `GOOGLE_APPLICATION_CREDENTIALS` |

The recorded legacy service-account identity is `gcpnew@easyfind-automations.iam.gserviceaccount.com`. The private key/JSON value is never stored in GitHub.

## Canonical EFPS inventory sheet

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Immutable row identity: `listing_id` in column `A`
- Physical contract: **48 columns, A:AV**

## Canonical schema

`schema.py` is the local source of truth for the physical sheet contract:

- physical column order and letters
- field names
- contract/extra/tail grouping
- owner of every column
- writable permissions
- explicitly defined allowed values
- row identity
- derived ranges
- integrity checks

The corrected contract includes `inventory_locked` at `AV`. The older legacy source file stopped at `AU`; the generated legacy `SHEET_CONTRACT.json` is the verified newer 48-column contract used to correct this repository.

## Cross-project ownership

- `panel`: A–AJ plus AP–AV
- `housing_agent`: AK–AM (`posted_url`, `posted_at`, `error_notes`)
- `meta_catalog`: AN–AO (`meta_catalog_id`, `meta_catalog_status`)

Rows are addressed by immutable `listing_id`, never by row position.

## Documentation impact for contract changes

Any change to the physical sheet contract must update, in the same implementation session:

1. `shared/google_sheets/schema.py` — canonical physical contract and checks.
2. `docs/DATA_CONTRACTS.md` — repository-level data contract.
3. `docs/ARCHITECTURE.md` — if ownership/boundary changes.
4. `docs/INFRASTRUCTURE.md` — if spreadsheet/runtime configuration changes.
5. `docs/OPEN_POINTERS.md` — if anything remains unverified.
6. `HANDOFF.md` — current implementation state.
7. All maintained root/`docs/` files must still be reviewed under the repository-wide documentation rule.

No second schema may be created in a module.
