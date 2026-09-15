# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current Inventory Management Phase 1 scope. Unknowns are never guessed. Future Meta Catalogue and Housing Portal additions are outside the current Phase-1 scope and are not treated as open pointers here.

## Runtime verification required

- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe remain `NOT VERIFIED`.
- Exact `inventory_locked` sheet control vocabulary remains `NOT VERIFIED`.

## Contract / implementation follow-up

- The successful WhAPI Cloudflare diagnostic required an explicit `User-Agent: EFPS-Inventory-Phase1/1.0`. The current `WhApiClient` source has not yet been changed to add that header. Decide and verify whether the explicit user-agent should become part of the canonical client transport contract before treating the client itself as production-accepted for live API calls.
- Google Maps `PARTIAL_MATCH` handling remains a production acceptance item. The current Stage-2 rule intentionally fails closed on non-`VERIFIED` Maps states; the 17 partial cases from the 25-row dry run must be analyzed before live extraction.

## Closed in the current deterministic contract pass

- `preferred_tenant_type` normalization is closed for the observed source variants: family variants normalize to `Family`; anyone/open-for-all variants normalize to `Open For All`.
- `pet_friendly` contract mismatch is closed. The deterministic last-resort rule now emits `Yes` when no pet restriction is mentioned and `No` for explicit no-pet wording, matching the observed application vocabulary.
- `servant_room` behavior is closed: explicit source `Yes` is preserved; missing source value defaults to `No`.
- `covered_parking` behavior is closed: Gated Community and Semi Gated default to `1` when no covered-parking value is supplied; Standalone does not receive that default.
- `internal_property_type` direct-field extraction and fallback behavior is closed. Explicit source values are normalized to the canonical three values; absent explicit values use the documented gating-wording fallback.
- `society_name` and `landmark` direct extraction/fallback behavior is closed. Direct values are preserved; missing values use the resulting location/locality, including after verified Maps locality resolution.
- `internal_property_type` → `society_amenities` is closed for the current deterministic contract: Gated Community and Semi Gated use the exact verified Sheet combinations; Standalone uses `-` when blank.
- Property subtype behavior is documented and regression-covered: explicit subtype is authoritative after alias normalization; `Apartment` is only the normal floor-bearing fallback; standalone wording does not invent Apartment.
- Property highlights and catalog title deterministic fallback behavior is documented and regression-covered. Explicit highlights/titles are preserved; otherwise only factual supported fragments/facts are used. AI remains optional wording-only processing.
- `age_of_property_years` remains non-blocking and conservative: it is populated only from an explicit/authoritative source fact and otherwise remains blank.
- The prior `furnish_type` mismatch remains closed: live Sheet values are exactly `Fully Furnished` and `Semi Furnished`; Unfurnished source wording leaves the field blank.
- Exact `bachelor_preference` vocabulary formatting remains closed. The live `Female Only ` trailing space is intentionally preserved.
- Exact live Sheet values and application dependencies for D, M, Y, Z, AA, AE, and AF remain verified.

## Deferred by current Phase-1 boundary

- Production WhAPI media downloads and direct Cloudinary association beyond the currently authorized temporary photo workflow.
- Inventory lifecycle/locking implementation beyond the current protected-column boundary.
- Additional batch/live orchestration beyond the explicit Phase-1 intake and processing paths.
- Future Meta Catalogue, Housing Portal, and website production integrations until their implementation requirements are explicitly authorized and established. These are future additions, not current open pointers.

## Governance

When any pointer is resolved, update this document and the affected architecture/contracts/handoff in the same implementation session.
