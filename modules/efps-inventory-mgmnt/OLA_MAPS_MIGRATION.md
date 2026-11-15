# Ola-only Maps migration - 2026-11-15

## Scope

Maps-only release, separated from the AI extraction prototype. Source/client Google links and the canonical google_maps_url field remain unchanged. No paid Google Maps or Places request implementation remains in the release sources. Existing Google secrets are retained for deferred cleanup, not consumed.

## Call sites and disposition

- `shared/google_maps/client.py`: one Google Geocoding transport replaced by an Ola-only compatibility shim. Old import name does not mean Google transport.
- `src/pipeline.py`: OlaInventoryMaps adapter, preserving source society/locality rather than overwriting from candidates. Link/address/pin status in processing notes.
- `src/notion_intake.py`: Google secret reader removed; runtime client uses configured Ola key. Unverified source link remains labelled unverified in caption.
- `src/extract.py`, `src/phase1.py`: pure link syntax helpers, no credentials or API calls.
- Internal repo website formatter `googlePlaces.ts`: five Google requests removed (new Places ID, legacy Details, new text search, forward geocode, reverse geocode). Formatter retains source facts and links, no longer invents identity/community from geocoded URLs. Browser code receives no Ola key.
- Internal formatter `formatterEngine.ts`: compatibility resolver now returns unresolved geography; parsed source details are not erased by unknown results.
- Both SAM templates: Google key/secret parameter bindings removed, isolated Notion secret-read permission removed. Ola remains configured. No secret deletion.
- Lambda package builder: no Google Maps package in isolated intake archive.
- UI source map anchor, catalogue link, schema and sanitizer URL handling: retained as links only.

## Active deployment scope checked

Render API shows CRM deployed from this internal repository. Live/development static websites use separate `efps-live-website` main/development. Full current archives of both website branches have zero Google Maps/Places endpoint/key/resolver hits. The formatter above exists in the internal repo and full legacy Lambda bundles, not proven active public website traffic. No website deployment change is required or made by this release.

Sydney has three Lambdas: efps-notion-intake plus Interactive and LeadWorker from efps-whapi-panel-v2. All carried Google key bindings before migration; full downloaded archives were inspected. Release packages replace Maps-related source only and preserve other code/dependencies. Compiled caches are excluded to avoid retaining old transport bytecode. The root CRM AI scheduler is untouched.

## Live provider caveat

Ola forward lookup of `SJR Pavillion, Bellandur, Bengaluru` returned a generic Bengaluru/Kanakapura 560056 result, not Bellandur. This is explicitly rejected as source-locality corroboration and never copied into the listing. The Google source short link is reachable and names the Bellandur place, but has no explicit safe pin coordinates. The pin remains unverified. The release removes the Google dependency; it does not claim provider capability equivalence or that all properties can be geographically verified.

Reverse geocoding uses the actual Ola `results` payload key, distinct from forward `geocodingResults`. An explicit URL place pin or coordinate query may be reverse-geocoded; a map camera center cannot.

## Validation before cutover

- 220 Python inventory/schema/Maps tests passed.
- Both SAM templates pass `sam validate --lint`.
- Node 24.21.0: root Vite build and 11 targeted inventory/Notion tests passed.
- Website formatter targeted TypeScript compilation passed in the prototype checkpoint; no subsequent TypeScript behavior change.
- Three prepared runtime ZIPs have zero paid Google Maps/Places endpoint strings in executable source.
- Restricted redirects, malformed coordinates, Google source-link preservation, generic-candidate rejection and differing forward/reverse payloads have regression tests.

Cutover and post-deploy evidence will be appended after actual execution. This pre-release section does not certify deployment. AI prototype/model benchmark remains separate and not deployed.

## Verified live cutover - 2026-11-15 14:12 IST

Both `efps-notion-property-intake` and `efps-whapi-panel-v2` are UPDATE_COMPLETE. All three Sydney Lambdas are Active / LastUpdateStatus Successful, with Ola configured and no GOOGLE_MAPS_API_KEY, GOOGLE_PLACES_API_KEY or MAPS_SECRET_ARN binding. Both stack parameter sets omit MapsSecretArn. Render CRM has no Google Maps key binding. Live/development public website source branches contain no paid Google Maps/Places requests.

Downloaded deployed archives were scanned again: zero paid Google Maps/Places endpoint strings in executable Python/TypeScript/JavaScript. Deployed code hashes:
- Notion intake: `Ly/uRWlrIyQNyMzudob7dR1ZANloyI1rhlxEk0/FYoY=`
- Interactive and LeadWorker: `yvlAc46NQMAwwbNyuELuVg5rdTBdtJffnCXSP77s7xg=`

Read-only replay using the downloaded production intake code plus live Ola against the current SJR raw text passed: Bellandur/SJR Pavillion/85000/original short link retained; Ola generic candidate rejected; pin not verified; caption labels original link not verified. This was not an actual Lambda invocation/end-to-end persisted intake test and did not modify the SJR listing or photos. Existing listing remains Pending with the same 10 URLs. No sends, catalogue actions, AI extraction activation or CRM scheduler changes.

PR #106 CI test/verify checks passed at source commit 64ee3ec. Node 24 build/targeted checks, SAM lint and post-release source regression passed. Final documentation-only commit adds this evidence. AI reader was declined at 14:11 IST, never model-tested/paid, and remains parked only on a local prototype branch. No AI prototype code in this Maps release.
