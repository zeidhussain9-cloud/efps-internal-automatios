# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current Inventory Management Phase 1 scope. Unknowns are never guessed. Future Meta Catalogue and Housing Portal additions are outside the current Phase-1 scope and are not treated as open pointers here.

## Runtime verification required

- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe remain `NOT VERIFIED`.
- Exact `inventory_locked` sheet control vocabulary remains `NOT VERIFIED`.

## Contract / implementation follow-up

- The successful WhAPI Cloudflare diagnostic required an explicit `User-Agent: EFPS-Inventory-Phase1/1.0`. The current `WhApiClient` source has not yet been changed to add that header. Decide and verify whether the explicit user-agent should become part of the canonical client transport contract before treating the client itself as production-accepted for live API calls.

## Deterministic audit status — 2026-09-15 final hardening

The current repository hardening state is **35 GREEN, 0 YELLOW, 0 RED** for the 35 deterministic-scope fields, plus 13 SYSTEM / OUT OF SCOPE. The 25-row read-only projection and production contract gate passed on the merged hardening commit, with zero contract failures and zero Sheet writes.

The previously demonstrated Maps, society, and bachelor RED states are closed by the merged contract hardening. The exact bachelor live dropdown remains `Female Only `, `Male Only`, `Open for both`, with the trailing space on `Female Only ` intentionally preserved. `Family` clears the dependent field; `Open For All` defaults to `Open for both`; explicit valid source evidence overrides the default.

Do not reopen Maps, society, or bachelor contracts without fresh regression evidence demonstrating a new contract violation.

## Closed deterministic contract findings

- `google_maps_url` source extraction and exact source preservation, including the observed `share.google` source form, are closed by projection evidence and regression coverage.
- `preferred_tenant_type -> bachelor_preference` dependency and exact live dropdown vocabulary are closed by the merged hardening state.
- `pet_friendly` contract is closed for explicit positive/negative source wording.
- `servant_room` behavior is closed.
- `covered_parking` behavior is closed and follows resolved `internal_property_type`.
- `internal_property_type` direct extraction/resolution is closed, including explicit negative gating and unresolved-no-evidence semantics.
- `society_name` direct extraction/fallback behavior is closed.
- `landmark` separation from Maps URLs is closed; landmark never inherits locality.
- Property subtype behavior is closed for the current operational contract.
- Property highlights and catalog title fallback behavior are closed.
- `age_of_property_years` remains non-blocking and conservative.
- `furnish_type` behavior is closed for the observed live contract.
- Maintenance business semantics are closed, including `Included + Water`.
- `society_amenities` dependency behavior is closed.
- `pincode` is explicitly non-blocking.

## Historical projection conflicts

The latest read-only projection identified populated historical Sheet differences in BHK, maintenance, internal property type, and property highlights. These remain documented as historical/source/display conflicts. They are not parser failures because `raw_message_text` is the source of truth; deterministic extraction must not be altered to reproduce stale persisted values.

## Deferred by current Phase-1 boundary

- Production WhAPI media downloads and direct Cloudinary association beyond the currently authorized temporary photo workflow.
- Inventory lifecycle/locking implementation beyond the current protected-column boundary.
- Additional batch/live orchestration beyond the explicit Phase-1 intake and processing paths.
- Future Meta Catalogue, Housing Portal, and website production integrations until their implementation requirements are explicitly authorized and established.

## Governance

When a deterministic pointer is resolved, update this document and the affected architecture/contracts/handoff in the same implementation session. The deterministic field contract, regression suite, handoff, and control matrix must remain synchronized with approved business-rule changes.
