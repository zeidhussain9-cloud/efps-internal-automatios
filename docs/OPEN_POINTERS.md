# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current EFPS reconciliation scope. The seven Lead/UI/authentication contract decisions were adjudicated on 2026-09-16 and are now closed in the repository. The Inventory AU/AV reservation decision is also closed at the repository contract level; historical live Sheet cleanup remains a separate controlled operation.

## Closed contract decisions — 2026-09-16

- Lead history uses Slack message/thread history; no `lead_history` modal.
- Lost-stage handling remains direct stage handling; no `lead_lost` modal or reason-submission flow.
- Audit timestamps are stored in UTC and displayed in IST.
- Dashboard identity is discovered through Slack history; no `DDB_SESSIONS` dashboard persistence.
- Newly created dashboards are not pinned.
- Digest uses the Slack-history discovery/update/post behavior.
- Webhook authentication occurs before the live gate, matching the inspected legacy repository behavior at `bd186c7c3418d633bca6766b1b92204c7a56d484`.
- Inventory `AU` (`source_group`) and `AV` (`inventory_locked`) are reserved/dummy columns. They remain in the 48-column physical contract, must remain blank, are not operator-editable, and are excluded from Inventory Stage-1/2 writes.

## Deferred runtime/configuration verification

- Lead worker compatibility, including stream coalescing, `NewImage` completeness, card timestamp handling, card create/update behavior, digest refresh, exception paths, and missing-Lead cases.
- Production `EFPS_DDB_PREFIX` value and resulting Lead table identities.
- Slack credential stored payload schema and runtime resolution of `SLACK_BOT_TOKEN` / `SLACK_SIGNING_SECRET`.
- Webhook credential stored payload schema and runtime resolution of `EFPS_WEBHOOK_TOKEN`.
- Executable Inventory Stage-1 → canonical current-main Stage-2 routing through the deployed/testable path.
- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe.
- Historical AU/AV live Sheet values still require the separate controlled cleanup procedure; no repository task authorizes live Sheet mutation.
- Google Maps network resolution after deterministic URL extraction.
- WhAPI live transport verification, including whether the observed diagnostic-required `User-Agent: EFPS-Inventory-Phase-1/1.0` should become part of the canonical client transport contract.

These items depend on the actual external/runtime environment. Unknown credential schemas and production configuration values must not be guessed.

## Inventory deterministic status

The canonical Phase-1 deterministic implementation remains on current `main` and is outside the Lead contract reconciliation. The repository Inventory boundary remains clean: reconciliation adapters do not import or restore legacy Inventory Stage-2 extraction, normalization, field-resolution, validation, or pipeline logic.

AU/AV are reserved at the repository contract level. `StoredSession.source_group` remains DynamoDB session metadata and is intentionally independent of the Sheet's AU column.

## Batch / operating contract

The canonical row path is `tools/run_phase1_rows.py --start-row <n> --end-row <m>`.

The batch runner performs one source-range read and one multi-range batch write. Google Sheets spreadsheet/worksheet objects are reused and rate-limit failures are retried with bounded exponential backoff. Already Processed rows are skipped, while a failed batch write does not mark prepared rows as processed, making the operation safe to rerun.

`tools/repair_phase1_dependencies.py` is the controlled repair path for already-processed rows after a manual property-type adjudication. It verifies the current property type, fills only blank dependent values, validates the repaired row, protects Stage-3 fields, and writes the repair through one batch request.

Field-level execution reporting exposes populated, blank, unresolved, and flagged fields, plus source segments, extracted candidates, and resolved selections.

## Governance

When a deterministic pointer is resolved, update this document and the affected architecture/contracts/handoff/control matrix in the same implementation session. Contract decisions and runtime verification status must remain synchronized with repository reality.
