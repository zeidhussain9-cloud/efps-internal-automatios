# Google Maps Shared Capability

Use `shared/google_maps` for reusable Maps technical operations.

## Rules
- Inventory/business modules decide when Maps is required.
- This capability resolves supplied Maps URLs/addresses and returns normalized location data.
- Never guess locality or pincode when Maps is unavailable.
- Runtime API access requires `GOOGLE_MAPS_API_KEY`; unverified runtime state remains explicit.
- Do not duplicate Maps API clients inside business modules.
