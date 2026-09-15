# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current Inventory Management Phase 1 scope. Unknowns are never guessed. Future Meta Catalogue and Housing Portal additions are outside the current Phase-1 scope and are not treated as open pointers here.

## Runtime verification required

- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe remain `NOT VERIFIED`.
- Exact `inventory_locked` sheet control vocabulary remains `NOT VERIFIED`.

## Contract / implementation follow-up

- The successful WhAPI Cloudflare diagnostic required an explicit `User-Agent: EFPS-Inventory-Phase1/1.0`. The current `WhApiClient` source has not yet been changed to add that header. Decide and verify whether the explicit user-agent should become part of the canonical client transport contract before treating the client itself as production-accepted for live API calls.

## Closed in the current contract reconciliation

- `furnish_type` contract mismatch is closed. Live Sheet values are exactly `Fully Furnished` and `Semi Furnished`; repository extraction, schema, and validation no longer create or accept `Unfurnished`. Unfurnished source text leaves `furnish_type` and `flat_furnishings` blank.
- `preferred_tenant_type` → `bachelor_preference` reconciliation is closed. The live Sheet vocabulary is authoritative: `Female Only `, `Male Only`, `Open for both`. Family/family-only with no explicit bachelor preference now leaves `bachelor_preference` blank rather than emitting the invalid intermediate `Not Allowed`. The `Family & Female Bachelors` legacy pattern and explicit female preference normalize to the exact live Sheet value `Female Only `, including its observed trailing space.
- `internal_property_type` → `society_amenities` reconciliation is closed. Gated Community now defaults to the exact live Sheet combination `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; Semi Gated defaults to the exact live Sheet combination `Security, Lift, CCTV, Power Backup`; Standalone does not invent amenities. Validation rejects nonblank amenity combinations outside the verified Sheet vocabulary.
- Exact `bachelor_preference` vocabulary formatting is closed. The repository intentionally preserves the live Sheet's `Female Only ` trailing space as part of the canonical contract and normalizes equivalent source wording to that exact value.
- Exact live Sheet values for `internal_property_type`, `furnish_type`, `preferred_tenant_type`, `bachelor_preference`, `society_amenities`, and `flat_furnishings` have been read-only verified. `pet_friendly` has no Sheet data-validation rule, but populated live values `Yes` and `No` were verified.
- No conditional/row-dependent Sheet dropdown validation was observed for the six dropdown-configured fields inspected. Their relationships are application/business dependencies, not conditional Sheet dropdown configuration.

## Deferred by current Phase-1 boundary

- Production WhAPI media downloads and direct Cloudinary association beyond the currently authorized temporary photo workflow.
- Inventory lifecycle/locking implementation beyond the current protected-column boundary.
- Additional batch/live orchestration beyond the explicit Phase-1 intake and processing paths.
- Future Meta Catalogue, Housing Portal, and website production integrations until their implementation requirements are explicitly authorized and established. These are future additions, not current open pointers.

## Governance

When any pointer is resolved, update this document and the affected architecture/contracts/handoff in the same implementation session.
