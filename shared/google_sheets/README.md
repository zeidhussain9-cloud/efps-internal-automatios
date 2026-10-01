# Google Sheets Shared Service

## Current verified repository state — 2026-10-01

This section is the current checkpoint for maintained documentation. Dated audit sections below remain historical evidence and are not silently rewritten.

- **Canonical UI/deployment branch:** `crm-ui-dashboard`
- **`crm-ui-dashboard` commit:** `da13083f6cb1f3c78ec3f4df661c515d43f556fa`
- **`crm-ui-dashboard` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **`main` reconciliation commit:** `692bdcbbab51752b8eb7d4927921d1cfc4830de7`
- **`main` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**; commit histories differ by design.
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, deployment `dep-dav55km0tbcc73eelat0`, **live**.
- **Production source:** `+919148338801`.
- **Supabase CRM:** 186 leads; 307 classifications; 20 pending; 186 promoted; 6,853 messages; 436 webhook events, 436 processed, 0 received, 0 processing, 0 failed.
- **AI persistence:** 196 AI runs, 196 proposed; 196 drafts; 186 AI cursors.
- **Inventory:** 88 active Housing rows; 1,333 sync-run records; latest recorded sync = 88 rows / 0 changed / 0 removed; AU/AV remain outside the CRM operational A:AT mirror.
- **Schedulers:** `crm_webhook_reconcile_1m` active every minute; `crm_inventory_sheet_reconcile_5m` active every five minutes.
- **P1–P5:** implemented and production-verified as documented in `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.
- **Verification:** `npm run build` PASS; `npm test` PASS (71/71); `npm run test:browser` PASS (1/1).
- **GitHub:** active remote UI branch search returns only `crm-ui-dashboard`; historical UI/inventory branches with deleted remotes are retained only as local historical evidence and are not active deployment branches.

### Current operational flow

```text
WhAPI +919148338801
  -> crm_webhook_events (persist + deduplicate)
  -> webhook processor/reconciler
  -> crm_messages + classification registry
  -> operator classification update
       -> non-qualified: remains outside CRM leads
       -> Qualified Lead: audited promotion transaction
            -> crm_leads + preserved messages
            -> webhook event lead linkage reconciled

CRM lead workspace
  -> complete chronological conversation + normalized requirements + evidence + notes + prior AI runs + cursor
  -> Bedrock primary / Sonnet fallback / Ollama fallback
  -> persisted crm_ai_runs + crm_drafts + provenance
  -> operator review/edit/pre-send grounding
  -> manual WhatsApp action only; no automatic send

Housing_Listings A:AV
  -> CRM reads operational A:AT only
  -> 88-row operational mirror in crm_inventory_snapshot
  -> five-minute reconciliation
  -> crm_inventory_sync_changes records future field-level changes
```

### Test-history checkpoint

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The final repository verification was 71/71 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.



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
