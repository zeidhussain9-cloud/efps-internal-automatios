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

## Remaining external dependencies — not open deterministic pointers

These are future live-runtime verification tasks, not unresolved Phase-1 implementation defects:

- Slack app installation, bot membership, command registration, deployed endpoint/signature verification, and live API probe.
- Exact `inventory_locked` live Sheet control vocabulary.
- Google Maps network resolution after deterministic URL extraction.
- WhAPI live transport verification, including whether the observed diagnostic-required `User-Agent: EFPS-Inventory-Phase1/1.0` should be made mandatory in the shared client.

They must not be mixed into the deterministic Phase-1 completion claim.

## Live-system migration reconciliation — 2026-09-16

The live-system migration is reconciled from the latest canonical `main`, not by merging the stale migration branch wholesale. Current `main` remains authoritative for Inventory Stage 1/2 and all newer Phase-1 hardening.

The approved live operational boundary now includes:

- Lead Management behavior, persistence, audit, cards, dashboard, stream worker, and Slack endpoints already present on `main`.
- The canonical WhAPI webhook boundary, with direct inbound traffic routed to Lead and the two configured inventory listeners routed only to Inventory Stage 1.
- `modules/efps-inventory-mgmnt/src/inventory_runtime.py` as the live Stage-1 durable intake adapter. It owns session capture/deduplication and delegates closed-session processing to the canonical `pipeline.process_closed_session()` implementation.
- `handler.py` as the scheduled Raw-row worker using only the canonical Inventory package.
- The SAM live-integration boundary, including the DynamoDB session-table ARN needed by the Stage-1 adapter.

No legacy Inventory extraction, normalization, field resolution, property processing, validation/business rules, or Stage-2 implementation is part of this migration.

The reconciliation is repository-level only. AWS deployment, Slack live registration, WhAPI destination cutover, production secret injection, synthetic live Inventory traffic, and old-runtime zero-traffic confirmation remain separate runtime acceptance gates.

## Verification / operating boundary

The canonical normal path is:

```bash
PYTHONPATH=.:modules/efps-inventory-mgmnt python tools/run_phase1_rows.py --start-row <n> --end-row <m>
```

The normal runner skips rows already marked `Processed`; already-processed rows use the controlled dependency-repair tool. Live production processing must start only from an exact local checkout of the accepted `main` commit and after the regression/audit suite passes locally.

No production credentials or secrets are part of the repository hardening.

## Shared Google Maps wrapper hardening — 2026-09-21

`shared/google_maps/client.py` now normalizes plain and Slack-wrapped Maps
links (`<URL|label>`) before extraction and resolution, and returns
`NOT_FOUND` without making a blank-query Google request when a short URL cannot
yield a usable query. Regression coverage is in
`shared/google_maps/test_google_maps.py` (12 tests passing). Both WhAPI and
Slack closed-session processing remain routed through the shared
`pipeline.process_closed_session()` Maps call; no flow-specific parser was
added. This is repository-level verification only; live runtime deployment
and Google API probing remain separate acceptance gates.

## Slack command surface reduction — 2026-09-21

`/efps fix` and `/efps verify` commands have been removed from the implementation.

**What was removed:**
- `/efps fix <listing_id> <field> <value>` — manual field correction command
- `/efps verify start|next|skip|exit|submit` — property verification workflow

**Rationale:**
These commands created a redundant correction/verification layer outside the authoritative Sheet. Properties requiring corrections should be edited directly in the Sheet or through future admin tools.

**Files modified:**
- `commands.py` — rewritten to handle only: `help`, `add-property`, `photos start`, `catalogue start|update`, `assign`, `status`, `show`, `run`
- `shared/slack/COMMANDS.md` — command table updated, removed commands documented
- `shared/slack/README.md` — command families list updated
- `shared/slack/CHANNELS.md` — verification channel marked retired
- `shared/slack/BATCH_OPERATIONS.md` — verify workflow section removed
- `shared/slack/NEW_USER_GUIDE.md` — fix/verify documentation removed
- `shared/slack/PROPERTY_VERIFICATION.md` — marked obsolete with explanation
- `shared/slack/RELEASE_GATE.md` — acceptance tests updated

**Current command surface:**
- `help` — usage guide
- `add-property` — new property intake
- `photos start` — photo collection workflow
- `catalogue start|update` — catalogue image management
- `assign <listing_id>` — retry collection assignment
- `status` — system status
- `show <listing_id>` — property details
- `run` — batch execution trigger

This is repository-level change only. Slack bot deployment, command registration, and live endpoint verification remain separate acceptance gates.

## Lead worker Lambda invocation — 2026-09-21

`/efps run` command now fully operational. The command invokes `EFPSLeadWorker` Lambda to trigger the lead ingestion worker on demand.

**What was fixed:**
- `template.yaml` Globals: Added `LEAD_WORKER_ARN` environment variable containing the ARN pattern for `EFPSLeadWorker` Lambda
- `template.yaml` EFPSCommands IAM policy: Added `lambda:InvokeFunction` permission scoped to `EFPSLeadWorker` function ARN pattern

**Verification:**
- `commands.py` `_run_worker()` function checks for `LEAD_WORKER_ARN` and invokes with `InvocationType=Event` (fire-and-forget)
- Error handling catches Lambda exceptions and returns user-friendly feedback
- Payload includes source metadata `{"source": "manual_slack_trigger"}`

Deployment note: SAM stack parameters must be supplied at deploy time; no default values are hardcoded. Once deployed, `/efps run` is available for manual lead worker triggers.

## Stale verify code and docs cleanup — 2026-09-21

Removed all remaining `/efps verify` dead code and stale documentation references.

**Code removed from `events_handler.py`:**
- `PROPERTY_VERIFICATION_CHANNEL` import
- `_verification_fields()` function
- `_save_verification()` function
- `write_phase1_update` and `process_phase1` imports (used only by the above)
- The `PROPERTY_VERIFICATION_CHANNEL` event listener branch in `_process_event()`
- Replaced listener block with a tombstone comment

**Docs updated:**
- `shared/slack/README.md` — removed `submit` from the listed session control words
- `shared/slack/NEW_USER_GUIDE.md` — section 8 rewritten with current session words per workflow; `submit` noted as removed
- `shared/slack/PHASE1_BOUNDARY.md` — workflow B changed from active verify description to REMOVED notice; required channels updated to remove `#epf-prop-aprovals`
- `shared/slack/IMPLEMENTATION_MAP.md` — `verify_session.py` row updated to REMOVED state
- `shared/slack/SLACK_APP_MANIFEST.md` — `usage_hint` updated to remove `fix` and `verify`, now reflects actual command surface
- `shared/slack/RELEASE_GATE.md` — `assign` command syntax corrected from `assign <user> to <listing_id>` to `assign <listing_id>`
- `HANDOFF.md` — `assign` syntax corrected in command surface list

**Current production-grade command surface (all 9):**
- `help`, `status`, `show`, `assign`, `run` — fully hardened, no open issues
- `add-property`, `photos start`, `catalogue start`, `catalogue update` — functionally hardened; session-initiation atomicity (post_message + DynamoDB write) is the one remaining non-atomic gap

Repository and documentation are now consistent with each other and with the live code.
