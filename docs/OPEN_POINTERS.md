## P1–P5 hardening closure — 2026-10-01

## Authoritative current closure — 2026-10-01

Evidence snapshot after final verification:
- crm-ui-dashboard commit: 252dad9e029d9c3d3ee8bd93be20c171f4099602
- crm-ui-dashboard tree: 375a701d907830a04ddd5f6d517f982ea729ed68
- main reconciliation commit: 918a9b9d1f010c144b400b01d23bad26ee061fb9
- main tree: 375a701d907830a04ddd5f6d517f982ea729ed68
- tree(main) == tree(crm-ui-dashboard): TRUE
- Render deployment: dep-dav71e0473hc73ahrnm0, status LIVE, commit 252dad9
- Production health: GET /health = HTTP 200, {"ok":true}
- Supabase: 186 leads, 6,870 messages, 465 webhook events, 310 classifications, 186 requirements, 196 AI runs, 196 drafts, 186 cursors, 88 active inventory rows
- Webhook events: 465/465 processed; 0 received; 0 processing; 0 failed
- Message reconciliation: 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0
- Historical classification population: 228/228 source="historical_extract"; 140/140 qualified mappings resolve to promoted leads
- Requirements: 186/186 lead rows have requirement rows; orphan/missing = 0
- AI/drafts: 196/196 draft→AI-run lead mappings valid; stale evidence references = 0; invalid cursor lead links = 0
- Inventory: 88 active rows; 71 Available; 17 Rented Out; invalid media-array rows = 0
- Cloudinary: 829/829 distinct production URLs returned HTTP 200 with image/* content-type using direct HEAD checks from the production-machine network path
- Tests: npm run build PASS; npm test 76/76 PASS; npm run test:browser 1/1 PASS
- Supabase Edge Function whapi-crm-webhook: ACTIVE version 8
- Legacy AWS webhook/handler files: no changes in the CRM hardening commit range
- 24-item audit status: GREEN / VERIFIED

Historical dated checkpoints below remain historical evidence; this block is the current source of truth.


> **Full-audit pointer — 2026-10-01:** `docs/audits/CRM_FULL_AUDIT_2026-10-01.md` is the current source for audit status. The last successful live DB snapshot during the audit recorded 6,859 messages and 454 webhook events. New code hardening is locally green (76/76 tests, 1/1 browser), and the latest Render deployment is live. Remaining evidence gates are Cloudinary timeouts/non-image response, authenticated duplicate-webhook replay, final production deployment, and main/tree reconciliation.

- P1 event-level lead linkage is reconciled during promotion and the 13 historical eligible rows were backfilled; current event/message lead mismatch is 0.
- P2 AU/AV are enforced as reserved and excluded from the operational A:AT CRM projection; no production Sheet values were mutated.
- P3 future inventory syncs record field-level change history in crm_inventory_sync_changes.
- P4 the one-minute webhook reconciler repairs message-backed received/processing states; current production checkpoint is 0 received/processing/failed.
- P5 disposable inventory create/edit/delete history regression is covered in tests without writing to the production Sheet.

These five audit findings are closed at the CRM implementation boundary. Historical pre-P3 inventory edits remain non-reconstructable, and AU/AV remain Sheet-owned metadata outside the CRM mirror.

## Current production closure — 2026-10-01

Verified in the final 2026-10-01 production-live audit checkpoint:

- Production source: `+919148338801`; `+917975102130` and `+919902024973` remain UI-visible but inactive.
- Webhook state: **436** persisted `crm_webhook_events`, **436 processed**, **0 received**, **0 processing**, **0 failed** at the post-hardening verification checkpoint.
- Live customer-number reconciliation: **28** distinct phones, **28/28** classified, **0** duplicate classification-per-phone groups, **0** phones mapped to multiple promoted leads.
- Lead/message integrity: **0** promoted messages missing their lead; **0** source/provider/message-ID reconciliation mismatches; **0** duplicate provider-event or source-message-ID groups.
- P1 historical event denormalization is closed: the 13 eligible pre-promotion rows were backfilled and current event/message lead mismatch is **0**.
- Housing inventory: **88** active listing IDs in the live `Housing_Listings` Sheet and **88** active CRM inventory rows. The live Sheet A:AT operational hash aggregate exactly matches the active Supabase inventory hash aggregate.
- Inventory cron: **1,336/1,336** executions succeeded, **0 failed** through `2026-10-01 12:10:00 UTC`; the latest production reconciliation returned **88 rows / 0 changed / 0 removed**.
- Current live Sheet observation: AU `source_group` is blank on all active rows; AV `inventory_locked` contains `Yes` on **43/88** active rows. P2 closes the CRM boundary: AU/AV are reserved and excluded from the A:AT mirror; no Sheet mutation was performed.
- Historical inventory edits before P3 remain non-reconstructable. New syncs record field-level old/new values in `crm_inventory_sync_changes`.

The full evidence is recorded in `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.

# Open Pointers

## Current verified repository state — 2026-10-01

This section is the current checkpoint for maintained documentation. Dated audit sections below remain historical evidence and are not silently rewritten.

- **Canonical UI/deployment branch:** `crm-ui-dashboard`
- **`crm-ui-dashboard` commit:** `da13083f6cb1f3c78ec3f4df661c515d43f556fa`
- **`crm-ui-dashboard` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **`main` reconciliation commit:** `692bdcbbab51752b8eb7d4927921d1cfc4830de7`
- **`main` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**; commit histories differ by design.
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, deployment `dep-dav55km0tbcc73eelat0`, **live**.
- **Production source:** `+919148338801`.
- **Supabase CRM:** 186 leads; 309 classifications; 20 pending; 186 promoted; 6,853 messages; 436 webhook events, 436 processed, 0 received, 0 processing, 0 failed.
- **AI persistence:** 196 AI runs, 196 proposed; 196 drafts; 186 AI cursors.
- **Inventory:** 88 active Housing rows; 1,333 sync-run records; latest recorded sync = 88 rows / 0 changed / 0 removed; AU/AV remain outside the CRM operational A:AT mirror.
- **Schedulers:** `crm_webhook_reconcile_1m` active every minute; `crm_inventory_sheet_reconcile_5m` active every five minutes.
- **P1–P5:** implemented and production-verified as documented in `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.
- **Verification:** `npm run build` PASS; `npm test` PASS (71/71); `npm run test:browser` PASS (1/1).
- **GitHub:** active remote UI branch search returns only `crm-ui-dashboard`; historical UI/inventory branches with deleted remotes are retained only as local historical evidence and are not active deployment branches.

### Current operational flow

```text
WhAPI +919148338801
  -> crm_webhook_events (persist + deduplicate)
  -> webhook processor/reconciler
  -> crm_messages + classification registry
  -> operator classification update
       -> non-qualified: remains outside CRM leads
       -> Qualified Lead: audited promotion transaction
            -> crm_leads + preserved messages
            -> webhook event lead linkage reconciled

CRM lead workspace
  -> complete chronological conversation + normalized requirements + evidence + notes + prior AI runs + cursor
  -> Bedrock primary / Sonnet fallback / Ollama fallback
  -> persisted crm_ai_runs + crm_drafts + provenance
  -> operator review/edit/pre-send grounding
  -> manual WhatsApp action only; no automatic send

Housing_Listings A:AV
  -> CRM reads operational A:AT only
  -> 88-row operational mirror in crm_inventory_snapshot
  -> five-minute reconciliation
  -> crm_inventory_sync_changes records future field-level changes
```

### Test-history checkpoint

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The final repository verification was 71/71 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.



## CRM production closure audit — 2026-10-01

Webhook reconciliation is now automatic via the production cron job. The 72-event current source audit is 72 processed / 0 received / 0 failed. The three classification queues are live. Privacy/authentication/RLS checks remain closed. Independent backup/restore remains blocked only by the need for an independently provisioned backup artifact and isolated restore target.

## Deferred external/runtime verification

- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe.
- `inventory_locked` live Sheet vocabulary is now verified as blank or `Yes`; 43 of 88 active rows currently contain `Yes`. Ownership/cleanup remains unresolved.
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
- [x] Audit the legacy Leads Tracker (`1GfM9lPQSukVpxCEVUlUDxFj_WYg0xQj8Inn7FA4sLVI`) as a current runtime dependency. It is accessible to the legacy service account, but no current executable repository reference or Render log hit was found; it is historical/documentation infrastructure, not the CRM runtime path.
- [x] Confirm the legacy Sheets sync is not part of the current CRM deployment. Historical `sync_to_sheet_v2.py` references remain only in extraction evidence/logs; current CRM uses WhAPI + Supabase for leads and the separate `Housing_Listings` Sheet for inventory.
- Housing column L has live header `w` while the canonical field is `google_maps_url`.
- Housing `listing_state` write ownership remains undecided.
- Housing AU/AV historical contents, if any, require controlled investigation; current contract says both are reserved/blank.
- Future webhook/import ingestion requires a stable external message/event identity and idempotent storage.
- D05 design remains proposed; the inventory audit informs it but does not approve it.

## Governance

When a deterministic pointer is resolved, update this document and the affected architecture/contracts/handoff/control matrix in the same implementation session. The deterministic field contract, regression suite, handoff, and control matrix must remain synchronized with approved business-rule changes.

## CRM gates — updated 2026-09-27

Hosted Ollama authentication and one fictional response are **verified**; these are no longer connectivity blockers. Remaining: representative fictional model-evaluation coverage, durable authenticated operator sessions, independent encrypted Supabase backup and isolated restore, stable-ID reconciliation of 735 leads / 23,454 conversations / 966 events against the curated subset, D06–D08 approvals, final credential rotation and controlled real-data import. Historical gate language; superseded on 2026-10-01 for the current CRM UI production path. Optional startup model smoke should be disabled after acceptance to avoid repeat inference costs. These CRM gates do not change Inventory Phase-1 business rules.


## Current CRM override — 2026-09-30\nThe older gate wording above is historical. The current production CRM source is +919148338801, reconciled Supabase data is live, and contact classification writes use CRM_CLASSIFICATION_WRITE_ENABLED with protected access. Remaining hardening items do not disable the current classification workflow.\n

## Current CRM closure — 2026-10-01

- Browser E2E regression fixed: the workspace request fixture now matches the query-string-bearing production route and the browser test signs in through the operator session flow.
- D07 Privacy, Safety & Operator Control is resolved in the application and design register.
- Current controls include protected sessions, default phone/message masking, reversible archive, global audit visibility, explicit export, retention/deletion boundaries, and offline/write gating.
- D08 remains the outstanding product/design handoff stage. Independent encrypted backup + isolated restore remains an infrastructure hardening item.
- Current CRM deployment branch remains `crm-ui-dashboard`.

## Current CRM closure audit — 2026-10-01

Current CRM implementation is production-live on `crm-ui-dashboard`. D06 and D07 are resolved; browser E2E is green; webhook reconciliation is automatic; classification queues are live; Leads Inbox timeline fields and server-side sorting are implemented.

Current CRM/product items still requiring explicit closure are:
- OOC service-area automation: the `Out of Coverage Area` / `OOC` status is implemented, but automatic geographic assignment is intentionally pending a deterministic coverage rule because several service areas are selective.
- D08 final visual/design-system handoff.
- Independent encrypted backup artifact and isolated restore proof.

The repository also contains older/historical planning checkboxes in the master plan and broader Inventory/external-runtime pointers. Those are not to be treated as current CRM implementation blockers without re-verification.

## 2026-10-01 production AI closure update

The former synthetic-only AI/live-data gate is superseded for the current CRM path. Production AI and database writes are enabled on Render service `srv-darsv560tbcc73cu4ip0`, and the production implementation uses complete lead history with normalized requirements, evidence, per-lead cursors, durable AI runs and versioned drafts. Remaining independent hardening items are encrypted backup/isolated restore, final credential rotation, and D08 visual/design handoff. Automatic WhatsApp sending remains disabled.

## 2026-10-01 — Current production checkpoint
Current CRM production is live on srv-darsv560tbcc73cu4ip0 at commit b61b4f7f686957c194094acec8638d7db602ec15. Remaining hardening: encrypted backup/restore proof, least-privilege AWS credential rotation, D08 handoff, incremental delta analysis and field-level AI proposal editing.

## 2026-10-01 — AI workspace follow-up

The saved-draft visibility defect is fixed in the source tree: persisted drafts are independently rendered and selectable after reload, with provider/model provenance. Migration 16 is live. The next production verification should exercise a real AI run through Render and confirm a new draft records `aws-bedrock` plus `au.anthropic.claude-opus-4-6-v1`; existing verified drafts are Ollama-era.

## 2026-10-01 — Approved AI improvements completed

Completed: stale-draft detection; model/provider provenance; draft evidence; deterministic pre-send grounding check; explicit AI outcome tracking; and explicit fallback-chain visibility. Incremental/delta message analysis remains deferred by operator decision. The Bedrock fallback is Claude Sonnet 4.6 using the AU geo inference profile, with Ollama retained as the final fallback.

## Final 24-item CRM audit closure — 2026-10-01

The earlier Cloudinary/idempotency/deployment/tree reconciliation pointers are superseded by the verified closure below.

- Live Supabase: 186 leads / 6,861 messages / 309 classifications / 196 AI runs / 196 drafts / 456 webhook events / 88 inventory rows.
- Historical classification baseline: 228/228 extracted; 140/140 historical qualified mappings valid; 0 non-qualified lead mappings.
- Requirements: 186/186 profiles; zero structural anomalies in the audited constraints.
- Webhook: 456/456 processed, zero pending/failed, zero duplicate provider IDs/fingerprints; authenticated replay returned already_processed with no row-count change.
- Cloudinary: 829/829 distinct URLs returned successful fl_getinfo metadata; zero timeouts/failures.
- Production: Render commit 252dad9e029d9c3d3ee8bd93be20c171f4099602, deployment dep-dav71e0473hc73ahrnm0, live; health HTTP 200.
- Tests: build PASS; 76/76 tests PASS; browser 1/1 PASS.
- Trees: origin/main tree == origin/crm-ui-dashboard tree == 375a701d907830a04ddd5f6d517f982ea729ed68.
- 24/24 CRM audit items: GREEN.
