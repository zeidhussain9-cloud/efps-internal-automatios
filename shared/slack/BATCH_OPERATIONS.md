# Slack Batch Operations

## Batch schedule recorded in the legacy system

The legacy template recorded three inventory batch schedules corresponding to approximately 08:00, 12:00 and 18:00 IST, plus a 09:00 IST lead digest. Treat these as legacy runtime configuration, not proof that the new repository is deployed on the same schedule.

## Batch controls

- `/efps status` — inspect Raw, Processed and Needs Review counts and batch state.
- `/efps run` — dispatch a batch immediately unless paused.
- `/efps pause` — disable scheduled inventory batch rules.
- `/efps resume` — re-enable scheduled inventory batch rules.

## What a batch does

The Slack command only dispatches the batch. The owning inventory pipeline performs the actual work.

For the current three-stage architecture:

1. **Stage 1 — Initial / Webhook:** collect property messages, delimit property sessions, create the raw canonical row.
2. **Stage 2 — Deterministic Extraction / Property Processing:** extract, normalize, resolve Maps when applicable, validate, optionally perform AI verification, then perform wording-only AI beautification where enabled and valid.
3. **Stage 3 — Downstream Operations:** operate Housing/Meta/lifecycle functions after the canonical row is ready.

Google Sheets is persistence/output, not a separate top-level stage. Google Maps is part of Stage 2, not a separate stage.

## Slack batch report

The legacy notifier sends one batch-level report rather than one Slack message per property. A report can include:

- processed count
- ready-to-publish count
- needs-review count
- duplicate count
- AI calls/model/cost information where available
- specific questions requiring human attention
- errors
- Housing_Listings link

A no-work batch may still post a healthy summary.

## Human review after a batch

When a batch produces review-required properties:

1. Read the batch report.
2. Open the property verification channel.
3. Run `/efps verify start`.
4. Work one property at a time in its thread.
5. Submit verified answers.
6. Re-check the canonical row.
7. Run the next batch only when operationally appropriate.

Do not treat a Slack report as the canonical state; use the inventory row for final state.

## Failure behavior

Legacy design intent:

- Slack notification failure should not break the property pipeline.
- Automatic runtime failures are recorded by the bug/crash mechanism.
- Slack-facing handlers return HTTP 200 after recording a failure to avoid retry storms.
- Unannounced bug records can be flushed on later batch activity or `/efps bugs`.

## Batch and photo relationship

Photo collection is currently separate from webhook property processing because inbound webhook media is not currently extracted into the row. A processed row can therefore enter the Slack photo queue after property processing.

Do not make photo presence a reason to duplicate the property row. Photo association is a same-row enrichment operation.
