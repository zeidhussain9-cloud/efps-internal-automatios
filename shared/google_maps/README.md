# Google Maps

Reusable technical capability for Maps URL extraction and Google Geocoding resolution.
Modules own property/business decisions; this package owns only API transport and normalized resolution.
Runtime requires `GOOGLE_MAPS_API_KEY`. Without it, resolution is explicitly `NEEDS_RUNTIME_VERIFICATION` and never guessed.
