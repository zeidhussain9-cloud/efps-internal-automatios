# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current Inventory Management Phase 1 scope. Unknowns are never guessed. Future Meta Catalogue and Housing Portal additions are outside the current Phase-1 scope and are not treated as open pointers here.

## Runtime verification required

- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe remain `NOT VERIFIED`.
- Exact `inventory_locked` sheet control vocabulary remains `NOT VERIFIED`.

## Contract / implementation follow-up

- The successful WhAPI Cloudflare diagnostic required an explicit `User-Agent: EFPS-Inventory-Phase1/1.0`. The current `WhApiClient` source has not yet been changed to add that header. Decide and verify whether the explicit user-agent should become part of the canonical client transport contract before treating the client itself as production-accepted for live API calls.

## Deterministic audit status — 2026-09-15

The deterministic field audit is now narrowed to one unresolved field:

- `google_maps_url` remains **RED pending the next rows 2:26 read-only projection**.
- The repository implementation now recognizes the observed `share.google` source URL form in the shared Maps adapter and production projection gate.
- The next projection is the acceptance evidence. If it passes, `google_maps_url` moves RED → GREEN. If it fails, it remains RED and only the demonstrated Maps failure is investigated.
- Previously closed GREEN deterministic fields must not be reopened without independent regression evidence.

## Closed deterministic contract findings

- `preferred_tenant_type` normalization is closed for the observed source variants.
- `pet_friendly` contract is closed for explicit positive/negative source wording.
- `servant_room` behavior is closed.
- `covered_parking` behavior is closed and follows resolved `internal_property_type`.
- `internal_property_type` direct extraction/resolution is closed, including explicit negative gating and unresolved-no-evidence semantics.
- `society_name` direct extraction/fallback behavior is closed.
- `landmark` separation from Maps URLs is closed.
- Property subtype behavior is closed for the current operational contract.
- Property highlights and catalog title fallback behavior are closed.
- `age_of_property_years` remains non-blocking and conservative.
- `furnish_type` behavior is closed for the observed live contract.
- Exact `bachelor_preference` vocabulary formatting remains closed.
- Maintenance business semantics are closed, including `Included + Water`.
- `society_amenities` dependency behavior is closed.
- `pincode` is explicitly non-blocking.

## Deferred by current Phase-1 boundary

- Production WhAPI media downloads and direct Cloudinary association beyond the currently authorized temporary photo workflow.
- Inventory lifecycle/locking implementation beyond the current protected-column boundary.
- Additional batch/live orchestration beyond the explicit Phase-1 intake and processing paths.
- Future Meta Catalogue, Housing Portal, and website production integrations until their implementation requirements are explicitly authorized and established.

## Governance

When the remaining Maps pointer is resolved, update this document and the affected architecture/contracts/handoff in the same implementation session. The deterministic field contract, regression suite, handoff, and control matrix must remain synchronized with approved business-rule changes.
