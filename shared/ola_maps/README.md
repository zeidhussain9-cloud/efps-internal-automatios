# shared/ola_maps

Reusable Ola Maps (Krutrim) technical adapter. Business decisions stay in modules;
this adapter only geocodes free text and returns structured results.

- Endpoint: `GET https://api.olamaps.io/places/v1/geocode?address=...`
- Credential: `OLA_MAPS_API_KEY` environment variable, or the approved local
  Keychain secret `efps-ola-maps-api-key`.
- `geocode()` never raises: failures return `confidence` of `NO_KEY`,
  `API_UNAVAILABLE`, or `ZERO_RESULTS` so intake is never blocked by a Maps outage.
- Used today by the Notion intake to normalize raw Location text onto the closest
  existing locality dropdown option (owner rule, 15 Nov 2026). Client-facing map
  links stay on Google Maps; Ola is background geo work only.
