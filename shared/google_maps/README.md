# Google Maps

Reusable technical capability for Maps URL extraction and Google Geocoding resolution.

Modules own property/business decisions; this package owns API transport and normalized resolution.

## Authentication

The current Inventory Phase-1 Maps credential is referenced by:

- Local macOS Keychain: account `efps`, service `efps-google-maps-api-key`
- Environment override: `GOOGLE_MAPS_API_KEY`

Credential priority:

1. Explicit constructor API key
2. `GOOGLE_MAPS_API_KEY`
3. Approved local Keychain credential

The raw API key MUST NOT be stored in Git.

The current key belongs to the Google Cloud project `easyfind-automations`, is identified in the non-secret registry as `Google Maps Key`, and is restricted to `geocoding-backend.googleapis.com`.

## Runtime behaviour

The adapter uses the Google Geocoding API endpoint:

`https://maps.googleapis.com/maps/api/geocode/json`

A missing credential returns `NEEDS_RUNTIME_VERIFICATION`; an empty result returns `NOT_FOUND`; a Google partial match returns `PARTIAL_MATCH`; a normal resolved result returns `VERIFIED`.

The adapter accepts:

- `maps.app.goo.gl`
- `goo.gl`
- `maps.google.com`
- `www.google.com/maps`
- `maps.google.com`

Short links are expanded when possible. URL queries may resolve from coordinates, `/maps/place/...`, or `q`/`query`/`destination` parameters. Address-only resolution is also supported.

`MapsResolution` is the normalized result containing `canonical_url`, `formatted_address`, `locality`, `pincode`, `latitude`, `longitude`, and `confidence`.

`GoogleMapsClient.resolve()` is intentionally keyword-only: use `resolve(maps_url=..., address=...)`.

For verified results, the canonical URL is generated from returned coordinates and `place_id` when available.

## Inventory integration boundary

Inventory Management owns when Maps is required. In Stage 2, `process_closed_session()` resolves a supplied/extracted Maps URL after deterministic extraction/normalization. A `VERIFIED` result updates `google_maps_url`, `locality`, and `pincode`. `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, `NOT_FOUND`, or an unrecognized state fails closed into `Needs Review`.

Maps is a Stage-2 processing sub-step, not a separate top-level stage.

## Verified runtime acceptance

The following application-path probes passed without exposing the key:

- Keychain credential loaded successfully.
- Address resolution for `Harlur, Bengaluru, Karnataka` returned `VERIFIED` with coordinates.
- A Google Maps search URL resolved to HSR Layout, Bengaluru, pincode `560102`, with `VERIFIED` confidence.
- The actual Inventory Stage-2 `process_closed_session()` path consumed the Maps result successfully and populated `locality`, `pincode`, and canonical `google_maps_url`.

These probes establish live Maps API access for the verified credential at the time of testing; they do not authorize storing the secret in the repository.

See `CREDENTIALS.md` for the non-secret credential registry.
