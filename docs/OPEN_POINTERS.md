# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current Inventory Management Phase 1 and live-system migration scope. Deterministic Phase-1 contract work is complete. Unknowns are never guessed. Future Meta Catalogue and Housing Portal additions are outside the current Phase-1 scope.

## Deferred external/runtime verification

- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe.
- Exact `inventory_locked` live Sheet control vocabulary.
- Google Maps network resolution after deterministic URL extraction.
- WhAPI live transport verification, including whether the observed diagnostic-required `User-Agent: EFPS-Inventory-1.0` should become part of the canonical client transport contract.
- Production deployment identity, final endpoint URLs, Lambda environment/secret injection, and DynamoDB `efps-sessions` availability for the Stage-1 runtime adapter.
- Synthetic live Inventory traffic through the final WhAPI destination and confirmation that the old runtime receives zero required traffic after cutover.

These items depend on the actual external/runtime environment. They are not unresolved Phase-1 field-resolution, normalization, validation, or Sheets-batch implementation defects.

## Phase-1 deterministic hardening status — 2026-09-15

The consolidated Phase-1 implementation is merged on `main`. The implementation has one canonical Phase-1 runner, deterministic Maps URL extraction, strict internal-property-type resolution from explicit source classification, coupled parking/amenity resolution, location fallbacks, immediate validation, status transitions, field-level reporting, deterministic traceability, controlled repair for already-processed rows, and quota-safe resumable Sheets processing.

The exact bachelor live dropdown remains `Female Only `, `Male Only`, `Open for both`, with the trailing space on `Female Only ` intentionally preserved. `Family` clears the dependent field; `Open For All` defaults to `Open for both`; explicit valid bachelor source evidence overrides the default.

## Closed deterministic contract findings

- `google_maps_url` source extraction and exact source preservation, including the observed `share.google` form, are closed by deterministic extraction and regression coverage.
- `preferred_tenant_type -> bachelor_preference` dependency and exact live dropdown vocabulary are closed.
- `pet_friendly` contract is closed for the current positive/negative wording contract.
- `servant_room` behavior is closed.
- `internal_property_type` resolves only to `Gated Community`, `Semi Gated`, or `Standalone`; explicit source classification wins; casing and ordinary spacing/hyphenation variations are accepted; missing or invalid classification remains unresolved and never implies `Standalone`.
- Society/community names are not property-type evidence and no society-learning registry is used.
- `covered_parking` defaults to `1` for Gated Community/Semi Gated when absent, while explicit counts (including counts greater than `1`) are preserved.
- `open_parking` defaults to `-` and is populated only from explicit source evidence.
- `society_amenities` is resolved from the internal property type using exact canonical Sheet vocabulary.
- The internal `parkingSocietyAmenitiesResolved` concept is implemented by the coupled deterministic resolver.
- `landmark` never receives a Google Maps URL and falls back to `locality` as the final deterministic fallback.
- `society_name` uses explicit society/community/building evidence first, later verified Maps place evidence when available at runtime, and locality only as the final deterministic fallback; the fallback is review-flagged.
- `pincode` is non-blocking and property age may remain intentionally blank.
- Persisted Stage-2 Sheet values are not deterministic evidence.
- The canonical contract remains exactly 48 fields A:AV.
- Deterministic validation runs immediately after projection and fails closed for invalid canonical values.
- AI verification/beautification remains after the deterministic boundary. `catalog_title` and `property_highlights` can be produced/worded by AI later; they are not Phase-1 blockers. Image URL association remains a separate media flow.

## Batch / operating contract

The canonical row path is `tools/run_phase1_rows.py --start-row <n> --end-row <m>`.

The batch runner performs one source-range read and one multi-range batch write. Google Sheets spreadsheet/worksheet objects are reused and rate-limit failures are retried with bounded exponential backoff. Already Processed rows are skipped, while a failed batch write does not mark prepared rows as processed, making the operation safe to rerun.

`tools/repair_phase1_dependencies.py` is the controlled repair path for already-processed rows after a manual property-type adjudication. It verifies the current property type, fills only blank dependent values, validates the repaired row, protects Stage-3 fields, and writes the repair through one batch request.

Field-level execution reporting exposes populated, blank, unresolved, and flagged fields, plus source segments, extracted candidates, and resolved selections.

## Live-system migration reconciliation — 2026-09-16

Repository reconciliation starts from the latest canonical `main`. The stale migration branch is not merged wholesale. Current Inventory Stage-1/Stage-2 remains authoritative.

Approved live-system responsibilities now represented in the repository include Lead Management, Slack endpoints, the WhAPI webhook boundary, the scheduled Raw-row worker, and the durable Inventory Stage-1 intake adapter. The Stage-1 adapter is responsible only for listener/session/raw-intake integration and delegates closed-session processing to the canonical existing Inventory pipeline.

Legacy Inventory extraction, normalization, deterministic business rules, field resolution, property processing, validation/business logic, and Stage-2 implementation are explicitly excluded.

The repository-level migration is complete only when the dedicated migration commit is verified. Production acceptance remains separate until deployment and live probes establish the runtime gates below.

## Governance

When a deterministic pointer is resolved, update this document and the affected architecture/contracts/handoff/control matrix in the same implementation session. The deterministic field contract, regression suite, handoff, and control matrix must remain synchronized with approved business-rule changes.
