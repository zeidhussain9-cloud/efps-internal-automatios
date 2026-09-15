# Google Maps Shared Capability

Use `shared/google_maps` for reusable Maps technical operations.

## Rules
- Inventory/business modules decide when Maps is required.
- This capability resolves supplied Maps URLs/addresses and returns normalized location data.
- `GoogleMapsClient.extract_url()` is the single deterministic source-URL recognizer.
- Deterministic extraction must capture supported Maps URL families directly from `raw_message_text` without network access and preserve the exact source URL apart from non-URL message wrappers/terminal punctuation.
- Source URL capture must not depend on short-link expansion or API availability.
- Runtime expansion/geocoding is a separate network-dependent enrichment step; an unverified runtime state must remain explicit.
- URL-like text after a Landmark marker belongs in `google_maps_url`, not `landmark`.
- Never guess locality or pincode when Maps is unavailable.
- Runtime API access requires `GOOGLE_MAPS_API_KEY`; unverified runtime state remains explicit.
- Do not duplicate Maps API clients inside business modules.
- Regression tests must cover supported hosts, source wrappers, terminal punctuation, and adjacent-text boundaries.
