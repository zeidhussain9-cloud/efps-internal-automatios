# Shared Slack Capability

This folder is the canonical home for Slack integration knowledge and reusable Slack transport capability in EFPS.

## Purpose

Slack is an operational control and notification surface. The shared capability owns Slack transport concerns: authentication loading, message posting, thread/reply handling, Block Kit/interactivity plumbing, channel routing primitives, safe text handling, and integration documentation.

Business modules own business decisions and workflows. A module may call this capability, but business rules must not be hidden inside the shared Slack layer.

## Current EFPS Slack topology

Workspace: **Easyfind Automation Updates** (`T0BNK5NCZL1`)

Legacy/current panel app recorded in the source repository: **EFPS Wapi Pannel** (`A0BTQGLKR4Z`), bot user `efps_intake` (`U0BTLM3BXB8`), bot ID `B0BT78HLSB1`.

Operational channels:

- `#eps-wapi-pannel` (`C0BTQGG8VT3`) — inventory operations, batch reports, property fixes and photo collection.
- `#efps-leads` (`C0BTM6PH55L`) — lead cards and lead dashboard.

Historical channels are documented separately. They are not automatically current.

## Important current rule: no society approval workflow

The legacy repository contains contradictory society-approval material. It is **obsolete and must not be carried into the new repository**.

There is no `/efps societies`, `/efps society`, society approval queue, or society approval card in the new architecture. Society information may be used as property data and deterministic dependencies, but it is not a separate Slack approval workflow.

## Current operational flow

### Property intake and batch processing

1. WhatsApp inventory messages arrive through Stage 1.
2. A completed property session creates/persists the raw inventory row.
3. Stage 2 performs deterministic extraction, normalization, Maps resolution, validation, optional AI verification, and wording-only beautification.
4. Batch execution produces an operational Slack report.
5. Rows needing human attention enter the property verification workflow.
6. Stage 3 downstream operations occur only after the canonical row is ready.

Slack is not a substitute for the pipeline and a Slack outage must not corrupt the canonical inventory row.

### Photo collection — current temporary operating model

The webhook currently does **not** extract and persist inbound photo binaries into the property row. Until direct webhook media extraction/association is implemented, Slack is the human-assisted bulk photo collection path.

1. `/efps photos start` selects the next eligible processed property with no Cloudinary URLs.
2. Slack posts the property card/message and records its thread timestamp.
3. The operator attaches the property's photos directly in that thread.
4. The operator replies with the bare word `done`.
5. The events/photo worker reads the thread attachments, uploads them to Cloudinary, preserves existing URLs, and writes the resulting URL list back to the **same listing row**.
6. The queue is recalculated from the sheet. A successfully completed property disappears from the no-photo queue.

See `REVERIFY_PHOTOS.md` for bulk operation and recovery details.

### Human property verification

Batch validation can leave a property requiring human review. `/efps verify start` selects the next review item, posts its questions in a thread, and collects answers. The operator replies `submit` to save direct corrections, re-run deterministic dependencies, validate the canonical row, and mark it ready according to the verification workflow. `skip`, `next`, and `exit` control the session.

See `PROPERTY_VERIFICATION.md` and `BATCH_OPERATIONS.md`.

## Command surface

Slack exposes one top-level slash command: `/efps`. Its subcommands are routed by EFPS code, not separately registered with Slack.

Current command families:

- `help`
- `status`
- `run`
- `show <listing_id>`
- `fix <listing_id> <field> <value>`
- `verify start|submit|next|skip|exit`
- `photos start|done|next|skip|exit`
- `pause`
- `resume`

The bare thread words `done`, `submit`, `next`, `skip`, and `exit` are session controls where applicable. They are not Slack slash commands.

## Capability boundary

Shared Slack may provide:

- Web API request transport.
- Token/signing-secret loading from the approved local Keychain secret reference or environment fallback.
- Message and thread posting.
- File/thread retrieval primitives needed by photo sessions.
- Interactivity/request parsing.
- Safe text and mention escaping.
- Channel constants/configuration references.
- Reusable formatting/Block Kit primitives.
- Operational documentation and manifest specification.

Shared Slack must not decide:

- Which inventory row is ready.
- Which property fields are valid.
- Which deterministic normalization rule applies.
- Whether a listing is approved for downstream publishing.
- How a lead changes stage.
- Whether a property needs human review.

Those decisions belong to the owning module and canonical contracts.

## Security

The canonical local Keychain service is `efps-whapi-panel-slack` under account `efps`. The historical AWS source was `easyfind/slack-api-credentials`. Never store Slack bot tokens, signing secrets, webhook secrets, private keys, or other credentials in this folder or in Git.

Slack request verification must validate the signing secret before processing interactive/event requests. Fail closed for invalid signatures.

## Source lineage

This capability was reconstructed from the legacy `efps-platform` Slack implementation and documentation, including its command router, photo session, verification session, notifications, lead cards/dashboard, infrastructure, and Slack manifest. Legacy contradictions were reviewed rather than copied blindly.

The legacy app manifest is retained as historical source material; see `SLACK_APP_MANIFEST.md` for the cleaned target specification and explicit exclusions.

## Verification state

This folder documents the intended/canonical integration and migration state. A documented Slack URL, channel ID, scope, or app identifier is not proof that the new repository is deployed with that configuration. Runtime deployment and live Slack API verification remain separate checks.
