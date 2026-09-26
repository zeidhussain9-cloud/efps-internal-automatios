# EFPS Internal Automations — Current Handoff

## Current state

The active workstream is **CRM source-of-truth reconciliation only**. Branch `crm/source-of-truth-reconciliation` is based on the canonical `main`. No CRM UI implementation, Figma editing, live customer/inventory connection, or Render repointing is part of this step.

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

## Verification / operating boundary

The canonical normal path is:

```bash
PYTHONPATH=.:modules/efps-inventory-mgmnt python tools/run_phase1_rows.py --start-row <n> --end-row <m>
```

The normal runner skips rows already marked `Processed`; already-processed rows use the controlled dependency-repair tool `tools/repair_phase1_dependencies.py`. Live production processing must start only from an exact local checkout of the accepted `main` commit and after the regression/audit suite passes locally.

No production credentials or secrets are part of the repository hardening.

## Live operational boundary

- Lead Management behavior, persistence, audit, cards, dashboard, stream worker, and Slack endpoints present on `main`.
- The canonical WhAPI webhook boundary, with direct inbound traffic routed to Lead and the two configured inventory listeners routed only to Inventory Stage 1.
- `modules/efps-inventory-mgmnt/src/inventory_runtime.py` as the live Stage-1 durable intake adapter. It owns session capture/deduplication and delegates closed-session processing to the canonical `pipeline.process_closed_session()` implementation.
- `handler.py` as the scheduled Raw-row worker using only the canonical Inventory package.
- The SAM live-integration boundary, including the DynamoDB session-table ARN needed by the Stage-1 adapter.

## CRM reconciliation state — 2026-09-26

Canonical CRM documentation is under `docs/crm/`; the two dated audits are preserved under `docs/audits/`.

Reconciled:
- `efps-internal-automatios` is the canonical CRM implementation repository.
- D01–D04 remain approved; D05 is proposed and informed by the verified Housing Listings audit.
- Figma is the working design environment; Canva remains the visual reference.
- Housing Inventory is the live `Housing_Listings` Google Sheet under the 48-field repository contract.
- Inventory Stage-1/2 write boundary is A:D and F:AO; AU/AV are reserved and blank.
- The legacy lead extraction, legacy `leads.db`, Leads Tracker, and current DynamoDB lead runtime are distinct layers that still require reconciliation before live CRM source selection.
- The current audit reports are evidence snapshots, not permission to mutate production data.

Open blockers are maintained in `docs/OPEN_POINTERS.md`.

Next ordered stage after this reconciliation branch: correct the approved Figma screens and design/approve D05. Implementation and Render deployment follow only after the UI design gate.

## Remaining external dependencies

These are future live-runtime verification tasks, not unresolved Phase-1 implementation defects:

- Slack app installation, bot membership, command registration, deployed endpoint/signature verification, and live API probe.
- Exact `inventory_locked` live Sheet control vocabulary.
- Google Maps network resolution after deterministic URL extraction.
- WhAPI live transport verification, including whether the observed diagnostic-required `User-Agent: EFPS-Inventory-Phase1/1.0` should be made mandatory in the shared client.

## Current Slack command surface

**Production-grade (5):**
- `help` — usage guide
- `status` — system status
- `show <listing_id>` — property details
- `assign <listing_id>` — retry collection assignment
- `run` — manual lead worker trigger (Lambda invocation)

**Functionally hardened (4):**
- `add-property` — new property intake
- `photos start` — photo collection workflow
- `catalogue start` — catalogue image management
- `catalogue update` — catalogue update workflow

**Known behaviour:** WhAPI returns `{"error": "operation_timeout"}` as an HTTP 200 on the PATCH `/business/collections/{id}` endpoint when its backend is slow. `assign_to_collection` now detects this and retries once with the same 10s backoff used for 429.

**Removed commands:** `/efps fix` and `/efps verify` removed 2026-09-21. Properties requiring corrections should be edited directly in the Sheet or through future admin tools.

## Active CRM UI handoff — 2026-09-27 (supersedes historical CRM-reconciliation-only heading)

- The **only** CRM UI development/deployment branch is `crm-ui-dashboard`. `main` is untouched and remains the separate Inventory/legacy branch.
- Render `easyfind-crm-d01-d05` successfully called hosted Ollama `gpt-oss:20b` with fictional `L-1001` at 2026-09-26 21:25:38 UTC. The five expected keys were returned. No local model.
- Dedicated root `steering.md` is the only CRM model system instruction, loaded and cached by `src/ollama-adapter.mjs` (2-KiB maximum). It conveys EFPS brokerage purpose, model role, structured extraction, operator control and no invented facts. Repository `CORE_STEERING.md` remains separate.
- Application tests, build, browser and GitHub Actions must pass on the new steering commit; Render `49b4f30` succeeded with the dedicated steering at 2026-09-26 21:36:16 UTC. Optional `CRM_OLLAMA_STARTUP_SMOKE_ENABLED=false` is deployed: `dep-das3lspa4omc738mqre0` live at 2026-09-26 21:37:57 UTC; no startup inference observed. On-demand fictional pilot remains enabled.
- No real customer data imported; Supabase still holds three fictional test leads and zero messages at last independent count. The historical source audit found 735 leads, 23,454 conversations and 966 events. D06–D08, backup/restore, source reconciliation, production auth and final credential rotation remain open.
