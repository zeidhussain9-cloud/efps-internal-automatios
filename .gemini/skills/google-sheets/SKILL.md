# Google Sheets Shared Skill — EFPS

## Purpose

Use this skill for any EFPS task involving the shared Google Sheets capability or the canonical `Housing_Listings` contract.

## Mandatory sources

Before implementation, verify:

1. `shared/google_sheets/README.md`
2. `shared/google_sheets/schema.py`
3. `docs/DATA_CONTRACTS.md`
4. `docs/INFRASTRUCTURE.md`
5. The applicable module guidance.

For legacy truth, refer to the verified `efps-platform` sources named in the local README rather than inventing a new schema or ownership rule.

## Canonical inventory sheet

- Spreadsheet ID: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`
- Worksheet: `Housing_Listings`
- Row identity: immutable `listing_id` in column `A`

## Credential boundary

The verified legacy AWS Secrets Manager secret is:

`efps-whapi-panel-sheet`

The legacy local-development variables are `GOOGLE_SERVICE_ACCOUNT_JSON` and `GOOGLE_APPLICATION_CREDENTIALS`. Never commit service-account JSON or private keys.

## Schema rule

`shared/google_sheets/schema.py` is the single local source for physical column order, names, ownership, writable permissions, allowed values, and derived ranges. Never duplicate these facts in a second schema.

When the sheet contract changes, update the schema first, then update affected module/docs/tests. A column owner or allowed-value change is a business decision, not a refactor.

## Documentation rule

For every schema or shared capability change, review all maintained root documents and all documents in `docs/`. At minimum, reconcile architecture, contracts, infrastructure, open pointers, local shared README, skill references, and `HANDOFF.md` as applicable.
