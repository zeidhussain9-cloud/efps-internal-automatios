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

`schema.py` is the single maintained source of truth for:

- physical column order and letters
- field names
- contract/extra/tail grouping
- owner of every column
- writable permissions
- explicitly defined allowed values
- row identity
- derived ranges
- row-width and ownership integrity checks

The corrected contract includes `inventory_locked` at `AV`. The older legacy source file stopped at `AU`; the generated legacy `SHEET_CONTRACT.json` is the newer 48-column contract used to correct this repository.

## Cross-project ownership

- `panel`: A–AJ plus AP–AV
- `housing_agent`: AK–AM (`posted_url`, `posted_at`, `error_notes`)
- `meta_catalog`: AN–AO (`meta_catalog_id`, `meta_catalog_status`)

The shared client enforces 48-column width for full-row operations. It does not perform business-level row lookup, duplicate handling, locking, or workflow transitions; those remain module responsibilities.

## Runtime status

The credential contract and client are implemented. Actual service-account authorization to the named spreadsheet and a safe live read/write smoke test remain runtime verification items.

## Documentation impact for contract changes

Any change to the physical sheet contract must update, in the same implementation session:

1. `shared/google_sheets/schema.py` — canonical physical contract and checks.
2. `shared/google_sheets/README.md` — local capability documentation.
3. `docs/DATA_CONTRACTS.md` — repository-level data contract.
4. `docs/ARCHITECTURE.md` — if ownership/boundary changes.
5. `docs/INFRASTRUCTURE.md` — if spreadsheet/runtime configuration changes.
6. `docs/OPEN_POINTERS.md` — if anything remains unverified.
7. `HANDOFF.md` — current implementation state.
8. All maintained root/`docs/` files must still be reviewed under the repository-wide documentation rule.

No second schema may be created in a module.
