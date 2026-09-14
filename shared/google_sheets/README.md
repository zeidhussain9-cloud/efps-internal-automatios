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

Business meaning, field ownership, validation, duplicate rules, and decisions about when to read or write remain with the owning module.

## Canonical EFPS inventory sheet

The verified legacy reference uses:

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Immutable row identity: `listing_id` in column `A`

These are identifiers, not secrets. fileciteturn315file0L2-L2

## Canonical schema source

The legacy `efps-platform` defines the physical Housing_Listings contract in `src/schema.py` (under `modules/efps-whapi-panel/` in that repository). It is the single source of truth for:

- physical column order and letters
- field names
- contract/extra/tail grouping
- owner of every column
- writable permissions
- allowed values where explicitly defined
- row identity
- derived write/read ranges
- integrity checks

The new shared Google Sheets layer must preserve that model rather than creating a second independent definition. The copied schema must be treated as a maintained cross-module contract source for this repository. fileciteturn313file0L2-L2

## Cross-project ownership verified from legacy

The legacy contract assigns:

- `panel`: A–AJ plus AP–AV
- `housing_agent`: AK `posted_url`, AL `posted_at`, AM `error_notes`
- `meta_catalog`: AN `meta_catalog_id`, AO `meta_catalog_status`

Rows are addressed by immutable `listing_id`; never by row position. fileciteturn322file0L2-L2

The machine-readable legacy export confirms a 48-column grid ending at `AV` and the exact writable fields for each owner. fileciteturn323file0L2-L2

## Credentials and AWS secret reference

The legacy implementation resolves the Google service-account credential from runtime configuration and, in deployment, from AWS Secrets Manager using secret name:

`efps-whapi-panel-sheet`

It also supports local-development `GOOGLE_SERVICE_ACCOUNT_JSON` or `GOOGLE_APPLICATION_CREDENTIALS`. fileciteturn315file0L2-L2

The service-account email recorded by the legacy code is:

`gcpnew@easyfind-automations.iam.gserviceaccount.com`

Do not copy the private key or JSON credential into this repository. fileciteturn328file0L2-L2

## Runtime boundary

This shared service provides Google Sheets technical access. The inventory module owns EFPS inventory workflows and decides when the sheet is read or written. The sheet contract itself remains centralized here so every module can consume the same ownership and column rules.
