# Google Maps

Reusable technical capability for Maps URL extraction and Google Geocoding resolution.

Modules own property/business decisions; this package owns only API transport and normalized resolution.

## Authentication

The approved Maps credential is referenced by:

- AWS Secrets Manager: `efps-google-maps-api-key`
- Local macOS Keychain: account `efps`, service `efps-google-maps-api-key`
- Environment override: `GOOGLE_MAPS_API_KEY`

Credential priority:

1. Explicit constructor API key
2. `GOOGLE_MAPS_API_KEY`
3. Approved local Keychain credential

The raw API key MUST NOT be stored in Git.

See `CREDENTIALS.md` for the non-secret credential registry.

## Runtime behaviour

Without an available credential, resolution remains `NEEDS_RUNTIME_VERIFICATION`.

The current Maps API key is restricted to the Google Geocoding backend.
