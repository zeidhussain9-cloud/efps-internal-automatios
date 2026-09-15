# Phase-1 Deterministic Inventory Boundary

## Canonical execution path

The production Phase-1 boundary is `src.phase1.run_phase1()`.

`run_phase1()` performs, in order:

1. Preserve the supplied `raw_message_text` as the authoritative source.
2. Segment the source into canonical source-message units.
3. Extract deterministic candidates.
4. Resolve canonical values without reading persisted Stage-2 Sheet values as evidence.
5. Apply deterministic normalization and dependency rules.
6. Execute deterministic Google Maps URL extraction. This step performs no network access.
7. Apply landmark and society fallback rules.
8. Run deterministic validation immediately after projection.
9. Set `intake_status=Processed` and `status=Pending` only when the Phase-1 projection is valid. Invalid canonical states become `Needs Review`.
10. Return field-level reporting and a trace containing source segments, extracted candidates, and resolved values.

The `src.pipeline.deterministic()` function delegates to the same projection boundary. Closed-session/live processing calls the same `run_phase1()` before any runtime Maps resolution or AI work.

## Canonical internal property type

The only accepted values are:

- `Gated Community`
- `Semi Gated`
- `Standalone`

Direct labelled source evidence wins over weaker evidence, with later source-message precedence. If source evidence is insufficient, the canonical community/property-type registry may adjudicate. Missing evidence never becomes `Standalone` by default.

## Coupled property-type state

The internal `parkingSocietyAmenitiesResolved` concept is implemented by the deterministic resolver `resolve_parking_society_amenities()` and covers one coupled state:

- Gated Community / Semi Gated + missing covered parking -> `1`
- Explicit covered parking counts are preserved, including values greater than `1`
- Missing open parking -> `-`
- Society amenities default from the internal property type using only the exact live Sheet dropdown combinations

## Location contract

`google_maps_url` is a deterministic source field. It is never written to `landmark`.

`landmark` uses explicit source evidence first and `locality` as the final deterministic fallback.

`society_name` uses explicit society/community/building evidence first. A later verified Maps place name may replace a locality fallback. Locality is the final fallback and is reported with `society_name_locality_fallback` for later review.

`pincode` is optional and non-blocking. `age_of_property_years` remains intentionally blank when no authoritative source fact exists. Image URLs are handled by the separate media flow.

## Google Sheets safety

The `GoogleSheetsClient` caches spreadsheet/worksheet objects, supports multi-range `batch_update`, and retries rate-limit failures with bounded exponential backoff.

The Phase-1 batch runner performs one range read followed by one batch write for the bounded row set. A failed write does not mark rows processed in memory; the same command can be rerun safely. Rows already at `intake_status=Processed` are skipped.

## Remaining-row command

After this hardening branch is merged to `main` and the local repository is synchronized, the production Phase-1 command for the remaining rows is:

```bash
cd /path/to/efps-internal-automatios
PYTHONPATH=.:modules/efps-inventory-mgmnt python tools/run_phase1_rows.py --start-row 12 --end-row 26
```

This command deliberately does **not** perform Google Maps network resolution or AI verification/beautification. It reports each row's populated, blank, unresolved, review-flag, and deterministic trace data.
