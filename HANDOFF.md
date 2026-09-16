# EFPS Internal Automations — Current Handoff

## Current state

The authorized implementation target is **Inventory Management Phase 1**. The workflow has three top-level stages: Stage 1 Initial/Webhook, Stage 2 Deterministic Extraction/Property Processing, and Stage 3 downstream boundary reserved for later consumers.

## Stage-2 implementation truth

- `extract.py` discovers deterministic source facts from completed `raw_message_text`.
- `source_segments.py` is the canonical source-message boundary parser for concatenated WhatsApp inventory messages.
- `field_resolution.py` is the canonical candidate-resolution layer for BHK, maintenance, and internal property type.
- `pipeline.py` is the authoritative deterministic processing boundary and passes resolved internal property type explicitly into normalization.
- `normalize.py` consumes canonical resolved property type and must not independently reclassify it.
- BHK preserves decimals and later explicit corrections.
- Maintenance requires maintenance-specific context, normalizes K/lakh units, independently evaluates inclusion, and preserves source qualifiers such as `+ Water`.
- Internal property type has exactly three business values: Gated Community, Semi Gated, and Standalone. Explicit source classification wins; casing and ordinary spacing/hyphenation variants are accepted; missing or invalid classification remains unresolved and never implies Standalone.
- Numeric balcony extraction covers explicit singular/plural source forms, including bare `Balcony` as one balcony.
- Explicit no-pet source wording is authoritative during final normalization.
- `📍 Landmark:` followed only by a Maps URL remains a blank landmark; the URL belongs to `google_maps_url`, and landmark never inherits locality.
- Existing Sheet Stage-2 values are never deterministic extraction input.
- `Needs Review` is governed by `docs/NEEDS_REVIEW_CONTRACT.md`; non-blocking field gaps do not become property-processing blockers by themselves, but they must still remain deterministic and contract-valid.

## Canonical dependency contract

```text
internal_property_type -> society_amenities
internal_property_type -> covered_parking (blank-only default)
furnish_type -> flat_furnishings (blank-only default)
preferred_tenant_type -> bachelor_preference
maintenance -> maintenance_included
built_up_area -> carpet_area (blank-only fallback)
monthly_rent -> security_deposit (month-based source form)
```

For tenant eligibility:

- `preferred_tenant_type` has exactly two live Sheet values: `Family` and `Open For All`.
- `Family` -> `bachelor_preference` is blank.
- `Open For All` -> `bachelor_preference` defaults exactly to the Sheet dropdown value `Open for both`.
- Explicit valid source evidence for `Female Only ` or `Male Only` overrides the default.
- `Female Only ` includes the intentional trailing space present in the live Sheet dropdown and that exact value is the canonical contract.

## Final hardening status — 2026-09-15

The final Phase-1 hardening is merged to `main`. The canonical deterministic path includes source-only evidence, explicit internal property-type classification without a society-learning registry, coupled parking/amenity resolution, location fallbacks, deterministic Maps URL extraction, immediate validation, deterministic reporting/traceability, and quota-safe resumable Sheets processing.

The controlled repair command `tools/repair_phase1_dependencies.py` is the only approved repair path for already-processed rows after a manual property-type adjudication. It reads one bounded range, changes only blank dependent fields, protects Stage-3 fields, validates the repaired rows, and writes one multi-range batch.

## Inventory data glance — rows 2–26

The supplied deterministic extraction snapshot is consistent with the Phase-1 dependency contract for the visible rows: `status=Pending`, `intake_status=Processed`, canonical internal property types, covered parking populated as required, open parking as `-`, and society amenities populated according to property type. `EF-2609-DPTV` contains a manually corrected deposit in the supplied snapshot; that is treated as a source-data correction, not a software defect.

Two rows use the intentionally allowed locality fallback for society/landmark (`EF-2609-DPTV`, `EF-2609-22H0`); this remains a review-quality signal for later Maps enrichment, not a Phase-1 contract failure. `pincode`, `age_of_property_years`, image URLs, publishing metadata, and other downstream fields remain outside the deterministic acceptance gate where the source/next-stage contract allows them to remain blank.

## Reserved Sheet columns — current control decision

AU (`source_group`) and AV (`inventory_locked`) remain physical columns in the 48-column `Housing_Listings` contract, but are reserved/dummy columns for future functionality. Both must remain blank. They are not operational inputs, not operator-editable, and not included in Inventory Stage-1/2 writes. Historical values are a separate controlled live-data cleanup task and are not modified by this repository change.

`StoredSession.source_group` remains intentionally preserved as DynamoDB session metadata because it is independent runtime/session state; it is no longer copied into AU.

## Remaining external dependencies — not open deterministic pointers

These are future live-runtime verification tasks, not unresolved Phase-1 implementation defects:

- Slack app installation, bot membership, command registration, deployed endpoint/signature verification, and live API probe.
- Exact Inventory reserved-column live Sheet state/clearance (historical AU/AV values require separate controlled cleanup).
- Google Maps network resolution after deterministic URL extraction.
- WhAPI live transport verification, including whether the observed diagnostic-required `User-Agent: EFPS-Inventory-Phase-1/1.0` should be made mandatory in the shared client.

They must not be mixed into the deterministic Phase-1 completion claim.

## Verification / operating boundary

The canonical normal path is:

```bash
PYTHONPATH=.:modules/efps-inventory-mgmnt python tools/run_phase1_rows.py --start-row <n> --end-row <m>
```

The normal runner skips rows already marked `Processed`; already-processed rows use the controlled dependency-repair tool. Live production processing must start only from an exact local checkout of the accepted `main` commit and after the regression/audit suite passes locally.

No production credentials or secrets are part of the repository hardening.

## Approved Lead reconciliation contracts — 2026-09-16

The reconciliation branch carries the following controller-approved Lead behavior:

- Lead history remains Slack message/thread history; no `lead_history` modal.
- Lost-stage interaction remains direct stage handling; no `lead_lost` modal or reason-submission flow.
- Audit presentation uses IST; audit storage remains UTC timestamps.
- Dashboard discovery remains Slack-history based; no `DDB_SESSIONS` dashboard persistence.
- Newly created dashboards are not pinned.
- Digest behavior remains the Slack-history discovery/update/post implementation.
- Webhook authentication follows the legacy repository ordering: authentication before the live gate.

These Lead contracts are separate from the Inventory Stage-2 deterministic implementation and do not authorize changes to canonical Inventory processing.

## Runtime verification status

The following remain unverified until executed against the target runtime/configuration: Lead worker compatibility, production `EFPS_DDB_PREFIX`, Slack credential payload schema, webhook credential payload schema, and executable Inventory Stage-1 to canonical Stage-2 routing.
