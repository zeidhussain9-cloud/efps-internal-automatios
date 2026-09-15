# EFPS Internal Automations — Gemini Operating Adapter

Gemini CLI work in this repository follows `CORE_STEERING.md` first and these repository rules second.

## Before every task

- Read and apply `CORE_STEERING.md`.
- Read `HANDOFF.md` and relevant `docs/` and local guidance.
- Establish verified repository/runtime truth before acting.
- Never guess or silently fill missing facts.
- For significant work, state the immediate plan, perform one logical step, verify it, then continue.

## Mandatory documentation rule

For **every implementation**, Gemini must review **all maintained root documents** and **all documents inside `docs/`** against the resulting repository reality.

Maintained root documents:

- `README.md`
- `CORE_STEERING.md`
- `AGENTS.md`
- `GEMINI.md`
- `HANDOFF.md`

Maintained `docs/` documents are defined by `docs/DOCUMENT_MAP.md`.

Every affected document must be updated in the same implementation. Documents not affected must still be checked for accuracy. Update `HANDOFF.md` when current task/session state changes.

Apply `docs/DOCUMENT_UPDATE_MATRIX.md` and `docs/DOCUMENT_GOVERNANCE.md` for detailed routing.

## Current architecture truth

- Root = AI/repository operation.
- `docs/` = canonical business/system truth.
- `modules/` = business capabilities.
- `shared/` = reusable technical capabilities.
- Established shared capability boundaries:
  - `shared/cloudinary/`
  - `shared/credentials/`
  - `shared/google_maps/`
  - `shared/google_sheets/`
  - `shared/slack/`
  - `shared/whatsapp_whapi/`

Inventory Phase 1 uses three top-level stages only: Initial/Webhook, Deterministic Extraction/Property Processing, and the Downstream Operations boundary. Maps and AI processing are Stage-2 sub-steps; Google Sheets is transport/output.

## Deterministic Inventory architecture

Stage 2 uses `raw_message_text` as its only deterministic extraction source. The flow is canonical source segmentation -> candidate extraction -> field resolution -> normalization -> validation -> Maps enrichment/verification -> optional AI review/wording.

`modules/efps-inventory-mgmnt/src/field_resolution.py` is the sole candidate-resolution layer for BHK, maintenance, and internal property type. `internal_property_type` has exactly three values: `Gated Community`, `Semi Gated`, and `Standalone`. `normalize.py` consumes the resolved value and does not independently classify property type.

### Required deterministic fallback and dependency contracts

- `society_name` is required whenever a usable location/locality exists. Resolution order is explicit society/apartment/community/building evidence first, then verified Maps/location enrichment, then the **ultimate fallback is the same resolved location/locality**. A blank society in that situation is a contract failure and must be treated as **RED**.
- `bachelor_preference` is interdependent with `preferred_tenant_type`. Direct valid source evidence has priority. `Family` requires a blank dependent value; `Open For All` deterministically defaults to the exact Sheet dropdown value `Open for both`. Explicit `Female Only` or `Male Only` source evidence overrides that default. Any non-canonical spelling or historical trailing-space variant is invalid.
- `google_maps_url` is deterministic source extraction, not network enrichment. The exact supported Maps URL found in `raw_message_text` must survive deterministic projection. `GoogleMapsClient.extract_url()` is the single URL-recognition source of truth; runtime short-link expansion/verification is separate and network-dependent. Any Step-4/source-preservation failure remains **RED** until the end-to-end path passes.
- A valid `property_subtype` such as `Independent House` is a successful direct subtype result and must not be regressed by an Apartment fallback.

### Deterministic Needs Review boundary

`docs/NEEDS_REVIEW_CONTRACT.md` is the canonical list of property-detail fields that can block a record with `Needs Review`. The blocking set covers property identity/type, location, core commercial terms, tenant eligibility, furnishing, size, bathrooms, and floor facts. Non-blocking fields remain deterministic and contract-valid but a blank or ordinary uncertainty in those fields alone must not force `Needs Review`.

This distinction is deliberate: `Needs Review` is a property-truth gate, not a catch-all for every optional, enrichment-owned, display, or downstream field. **Non-blocking does not mean ignored or permitted to be incorrect.**

Existing persisted Stage-2 Sheet values are never extraction input. The read-only model audit reports populated Sheet mismatches as source conflicts and does not overwrite the Sheet.

## Verification status

The repository-level architecture and regression contract are implemented. Production extraction remains gated on final post-change repository test execution and the read-only model audit. Google Sheets/Maps runtime capability verification remains separate from source-code verification. Other runtime capabilities remain explicitly unverified until their target-runtime probes succeed.

## Gemini-specific maintenance

`GEMINI.md` is a live operating adapter. Update it when Gemini workflow, repository layout, or mandatory Gemini-specific operating requirements change.

## Session procedure

Use `.gemini/skills/session-start/SKILL.md` at session start and `.gemini/skills/session-end/SKILL.md` at session end. Use the applicable repository-wide and custom skills for verification, planning, documentation, and capability-specific work.

## Security

Never commit secrets, API tokens, passwords, private keys, or production authentication material.
