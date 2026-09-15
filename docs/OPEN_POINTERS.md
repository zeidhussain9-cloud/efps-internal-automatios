# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current Inventory Management Phase 1 scope. Unknowns are never guessed. Future Meta Catalogue and Housing Portal additions are outside the current Phase-1 scope and are not treated as open pointers here.

## Runtime verification required

- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe remain `NOT VERIFIED`.
- Exact `inventory_locked` sheet control vocabulary remains `NOT VERIFIED`.

## Contract / implementation follow-up

- The successful WhAPI Cloudflare diagnostic required an explicit `User-Agent: EFPS-Inventory-Phase1/1.0`. The current `WhApiClient` source has not yet been changed to add that header. Decide and verify whether the explicit user-agent should become part of the canonical client transport contract before treating the client itself as production-accepted for live API calls.

## Closed in the current deterministic contract pass

- `preferred_tenant_type` normalization is closed for the observed source variants: family variants normalize to `Family`; anyone/open-for-all variants normalize to `Open For All`.
- `pet_friendly` contract is closed: explicit no-pet wording emits `No`; absence of a pet restriction emits `Yes` as the established last-resort rule.
- `servant_room` behavior is closed: explicit source `Yes` is preserved; missing source value defaults to `No`.
- `covered_parking` behavior is closed: Gated Community and Semi Gated default to `1` when no covered-parking value is supplied; Standalone does not receive that default.
- `internal_property_type` direct-field extraction is closed: explicit source values are accepted with common label separators and normalized to the canonical three values; absent explicit values use the documented gating-wording fallback.
- `society_name` and `landmark` direct extraction/fallback behavior is closed: direct values are preserved after presentation cleanup; placeholder-only values fall back to location/locality.
- `internal_property_type` → `society_amenities` is closed: Gated Community and Semi Gated use exact verified Sheet combinations; Standalone uses `-` when blank.
- Property subtype behavior is closed for the current Phase-1 contract: explicit subtype is authoritative after alias normalization; `Apartment` is only the normal floor-bearing fallback; standalone wording does not invent Apartment.
- Property highlights and catalog title fallback behavior is closed for the current deterministic contract: explicit values are preserved; otherwise only factual supported fragments are generated. AI remains optional wording-only processing.
- `age_of_property_years` remains non-blocking and conservative: populate only from an explicit/authoritative source fact; otherwise blank.
- The `furnish_type` mismatch is closed: live Sheet values are exactly `Fully Furnished` and `Semi Furnished`; Unfurnished source wording leaves the field blank.
- Exact `bachelor_preference` vocabulary formatting remains closed. The live `Female Only ` trailing space is intentionally preserved.
- Exact live Sheet values and application dependencies for D, M, Y, Z, AA, AE, and AF remain verified.
- Maps status handling is closed for deterministic extraction: `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, and `NOT_FOUND` are recorded as issues but do not by themselves convert a valid deterministic extraction to `Needs Review`. `Needs Review` is reserved for deterministic validation errors or explicit AI conflicts.

## Deferred by current Phase-1 boundary

- Production WhAPI media downloads and direct Cloudinary association beyond the currently authorized temporary photo workflow.
- Inventory lifecycle/locking implementation beyond the current protected-column boundary.
- Additional batch/live orchestration beyond the explicit Phase-1 intake and processing paths.
- Future Meta Catalogue, Housing Portal, and website production integrations until their implementation requirements are explicitly authorized and established. These are future additions, not current open pointers.

## Governance

When any pointer is resolved, update this document and the affected architecture/contracts/handoff in the same implementation session.
