## Current production closure — 2026-10-01

Verified after the automatic webhook reconciliation hardening:

- Render service: `easyfind-crm-d01-d05` (`srv-darsv560tbcc73cu4ip0`), branch `crm-ui-dashboard`.
- Current deploy: `dep-daumf68473hc739qdkd0`, commit `56e8f17216102fadc801a6f84470783160ca38dc`.
- Production source: `+919148338801`; `+917975102130` and `+919902024973` remain UI-visible but inactive.
- Current CRM state: 185 leads, 288 classifications, 13 pending, 2 explicitly unqualified, 185 promoted, 6,620 messages.
- Webhook state: 72 persisted events, 72 processed, 0 received, 0 failed.
- Automatic reconciliation is now a production database job: `crm_webhook_reconcile_1m`, every minute, calling `crm_reconcile_received_webhooks()`. A live cron execution succeeded and processed an event.
- Manual webhook reconciliation is no longer an operating requirement.
- The three Contact Classification queues are implemented: Not pushed to CRM, Qualified lead pushed to CRM, and Unqualified leads.
- Independent backup/restore remains the only item requiring external provisioning/approval; the repository's encrypted backup and approval-gated restore tooling is already implemented.


# Open Pointers

## CRM production closure audit — 2026-10-01

Webhook reconciliation is now automatic via the production cron job. The 72-event current source audit is 72 processed / 0 received / 0 failed. The three classification queues are live. Privacy/authentication/RLS checks remain closed. Independent backup/restore remains blocked only by the need for an independently provisioned backup artifact and isolated restore target.

## Deferred external/runtime verification

- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe.
- Exact `inventory_locked` live Sheet control vocabulary.
- Google Maps network resolution after deterministic URL extraction.
- WhAPI live transport verification, including whether the observed diagnostic-required `User-Agent: EFPS-Inventory-1.0` should become part of the canonical client transport contract.
- Production deployment identity, final endpoint URLs, Lambda environment/secret injection, and DynamoDB `efps-sessions` availability for the Stage-1 runtime adapter.
- Synthetic live Inventory traffic through the final WhAPI destination and confirmation that the old runtime receives zero required traffic after cutover.

These items depend on the actual external/runtime environment. They are not unresolved Phase-1 field-resolution, normalization, validation, or Sheets-batch implementation defects.

## Phase-1 deterministic hardening status — 2026-09-15

The consolidated Phase-1 implementation is merged on `main`. The implementation has one canonical Phase-1 runner, deterministic Maps URL extraction, strict internal-property-type resolution from explicit source classification, coupled parking/amenity resolution, location fallbacks, immediate validation, status transitions, field-level reporting, deterministic traceability, controlled repair for already-processed rows, and quota-safe resumable Sheets processing.

The exact bachelor live dropdown remains `Female Only `, `Male Only`, `Open for both`, with the trailing space on `Female Only ` intentionally preserved. `Family` clears the dependent field; `Open For All` defaults to `Open for both`; explicit valid bachelor source evidence overrides the default.

## Closed deterministic contract findings

- `google_maps_url` source extraction and exact source preservation, including the observed `share.google` form, are closed by deterministic extraction and regression coverage.
- `preferred_tenant_type -> bachelor_preference` dependency and exact live dropdown vocabulary are closed.
- `pet_friendly` contract is closed for the current positive/negative wording contract.
- `servant_room` behavior is closed.
- `internal_property_type` resolves only to `Gated Community`, `Semi Gated`, or `Standalone`; explicit source classification wins; casing and ordinary spacing/hyphenation variations are accepted; missing or invalid classification remains unresolved and never implies `Standalone`.
- Society/community names are not property-type evidence and no society-learning registry is used.
- `covered_parking` defaults to `1` for Gated Community/Semi Gated when absent, while explicit counts (including counts greater than `1`) are preserved.
- `open_parking` defaults to `-` and is populated only from explicit source evidence.
- `society_amenities` is resolved from the internal property type using exact canonical Sheet vocabulary.
- The internal `parkingSocietyAmenitiesResolved` concept is implemented by the coupled deterministic resolver.
- `landmark` never receives a Google Maps URL and falls back to `locality` as the final deterministic fallback.
- `society_name` uses explicit society/community/building evidence first, later verified Maps place evidence when available at runtime, and locality only as the final deterministic fallback; the fallback is review-flagged.
- `pincode` is non-blocking and property age may remain intentionally blank.
- Persisted Stage-2 Sheet values are not deterministic evidence.
- The canonical contract remains exactly 48 fields A:AV.
- Deterministic validation runs immediately after projection and fails closed for invalid canonical values.
- AI verification/beautification remains after the deterministic boundary. `catalog_title` and `property_highlights` can be produced/worded by AI later; they are not Phase-1 blockers. Image URL association remains a separate media flow.

## Batch / operating contract

The canonical row path is `tools/run_phase1_rows.py --start-row <n> --end-row <m>`.

The batch runner performs one source-range read and one multi-range batch write. Google Sheets spreadsheet/worksheet objects are reused and rate-limit failures are retried with bounded exponential backoff. Already Processed rows are skipped, while a failed batch write does not mark prepared rows as processed, making the operation safe to rerun.

`tools/repair_phase1_dependencies.py` is the controlled repair path for already-processed rows after a manual property-type adjudication. It verifies the current property type, fills only blank dependent values, validates the repaired row, protects Stage-3 fields, and writes the repair through one batch request.

Field-level execution reporting exposes populated, blank, unresolved, and flagged fields, plus source segments, extracted candidates, and resolved selections.

## Live-system migration reconciliation — 2026-09-16

Repository reconciliation starts from the latest canonical `main`. The stale migration branch is not merged wholesale. Current Inventory Stage-1/Stage-2 remains authoritative.

Approved live-system responsibilities now represented in the repository include Lead Management, Slack endpoints, the WhAPI webhook boundary, the scheduled Raw-row worker, and the durable Inventory Stage-1 intake adapter. The Stage-1 adapter is responsible only for listener/session/raw-intake integration and delegates closed-session processing to the canonical existing Inventory pipeline.

Legacy Inventory extraction, normalization, deterministic business rules, field resolution, property processing, validation/business logic, and Stage-2 implementation are explicitly excluded.

The repository-level migration is complete only when the dedicated migration commit is verified. Production acceptance remains separate until deployment and live probes establish the runtime gates below.

## CRM source-of-truth reconciliation — 2026-09-26

Open blockers before CRM live-data integration:

- Legacy `leads.db` (23,454 conversation rows) does not reconcile with the 6,064-message extraction evidence.
- Legacy `leads.db` has not been reconciled with current master DynamoDB lead-domain tables.
- Current Leads Tracker ownership/update mechanism must be verified as an ongoing operating source.
- Legacy Sheets sync clears/rewrites operational tabs and is unsuitable as a CRM write path.
- Housing column L has live header `w` while the canonical field is `google_maps_url`.
- Housing `listing_state` write ownership remains undecided.
- Housing AU/AV historical contents, if any, require controlled investigation; current contract says both are reserved/blank.
- Future webhook/import ingestion requires a stable external message/event identity and idempotent storage.
- D05 design remains proposed; the inventory audit informs it but does not approve it.

## Governance

When a deterministic pointer is resolved, update this document and the affected architecture/contracts/handoff/control matrix in the same implementation session. The deterministic field contract, regression suite, handoff, and control matrix must remain synchronized with approved business-rule changes.

## CRM gates — updated 2026-09-27

Hosted Ollama authentication and one fictional response are **verified**; these are no longer connectivity blockers. Remaining: representative fictional model-evaluation coverage, durable authenticated operator sessions, independent encrypted Supabase backup and isolated restore, stable-ID reconciliation of 735 leads / 23,454 conversations / 966 events against the curated subset, D06–D08 approvals, final credential rotation and controlled real-data import. Keep `CRM_REAL_DATA_ENABLED` and `CRM_DB_WRITE_ENABLED` disabled. Optional startup model smoke should be disabled after acceptance to avoid repeat inference costs. These CRM gates do not change Inventory Phase-1 business rules.


## Current CRM override — 2026-09-30\nThe older gate wording above is historical. The current production CRM source is +919148338801, reconciled Supabase data is live, and contact classification writes use CRM_CLASSIFICATION_WRITE_ENABLED with protected access. Remaining hardening items do not disable the current classification workflow.\n