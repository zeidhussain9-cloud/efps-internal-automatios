# Deterministic Extraction Review — 2026-09-15

## Evidence reviewed

The 25-row read-only production projection was reviewed against the raw WhatsApp source for rows 2–26. Existing Sheet values were treated as display-only and not as extraction evidence.

## Confirmed root causes

### `pet_friendly`
The source uses forms such as `Pets: Not Allowed`. The negative-expression regex did not permit the label delimiter (`:`), so the negative phrase was not matched and the fallback returned `Yes`.

**Permanent fix:** accept `:`, `=` and `-` after the Pets/Animals label; explicit negative evidence wins over positive/default behavior.

### `balconies`
The extractor only recognized a numeric form such as `2 Balconies`. Source rows also use the singular form `Balcony`, which carries an explicit count of one.

**Permanent fix:** recognize singular `Balcony` and normalize it to `1`; numeric counts continue to win.

### `landmark` vs `google_maps_url`
Some source records use `📍 Landmark:` followed by a Maps URL on the next line. A generic label extractor could interpret the URL as landmark text.

**Permanent fix:** `📍` markers are structured source anchors; Maps URLs belong to `google_maps_url`, never `landmark`. Any Maps URL found in the landmark candidate is discarded from `landmark`.

### `society_name` and `google_maps_url`
The EFPS source commonly uses `📍 Society Name:` followed by a Maps URL. This is a source grammar, not a generic labelled field. The deterministic extractor now treats the marker name as the society candidate and the URL as Maps data. The locality fallback remains a last resort after extraction/enrichment.

### `internal_property_type`
Explicit source syntax such as `Gated: Community` must resolve to `Gated Community`. The resolver was hardened to parse the explicit gated/semi-gated delimiter form and to preserve explicit standalone evidence. Missing evidence still cannot truthfully prove Standalone; the canonical schema fallback remains documented until Maps enrichment can establish a different classification.

## Business rules preserved

- Operational subtype usage is primarily `Apartment`, `Villa`, and `Studio`.
- `Duplex Villa` resolves to `Villa`.
- `1 RK` / `Studio` resolves to `Studio`.
- Normal apartment/building inventory resolves to `Apartment` unless a stronger supported subtype is present.
- `Maintenance: Included` → `maintenance=0`, `maintenance_included=Yes`.
- `Maintenance: Included + Water` → included=yes with the water-charge qualifier retained.
- Explicit maintenance amount → amount in `maintenance`, `maintenance_included=No`.
- Gated/Semi Gated → covered parking defaults to `1` when no explicit covered count exists.
- Pincode is non-blocking; blank pincode must not by itself create `Needs Review`.

## Dependency rule

`society_amenities` and `covered_parking` remain downstream of `internal_property_type`. They must not be independently inferred in a way that masks an upstream classification failure.

## Regression coverage

`tools/test_deterministic_edge_cases.py` covers the confirmed source forms for gated classification, subtype mapping, pet restrictions, singular balcony, Maps URL separation, society marker parsing, maintenance inclusion semantics, and covered-parking dependency.
