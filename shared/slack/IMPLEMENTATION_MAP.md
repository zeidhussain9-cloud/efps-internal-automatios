# Slack Phase-1 Implementation Map

This maps the legacy Slack behavior to the new repository without copying obsolete business workflows.

## Legacy → new ownership

| Legacy source | New location / responsibility |
|---|---|
| `modules/efps-whapi-panel/src/commands.py` | `shared/slack/COMMANDS.md` for transport-facing command surface; inventory module owns actual inventory actions |
| `photo_session.py` | `shared/slack/PHASE1_BULK_PHOTOS.md` for operator contract; inventory/media owners implement row selection and Cloudinary persistence |
| `verify_session.py` | `shared/slack/PROPERTY_VERIFICATION.md` for operator contract; inventory module owns correction/revalidation |
| `notify.py` | `shared/slack/client.py` for reusable Slack transport |
| `lead_card.py` / `digest.py` | Lead-specific Slack behavior; retained as capability knowledge and outside inventory-only completion gate |
| `SLACK_APP_MANIFEST.md` | `shared/slack/SLACK_APP_MANIFEST.md` |
| legacy infrastructure/channel records | `shared/slack/CHANNELS.md` and `shared/slack/routing.py` |

## Architectural rule

The new `shared/slack/` layer provides reusable technical Slack capability. It must not own inventory extraction, normalization, Maps decisions, verification eligibility, or publishing decisions.

The inventory module owns the deterministic row-processing workflow described in the canonical Stage-1/Stage-2 architecture.

## Photo implementation boundary

The legacy `photo_session.py` contains the critical Phase-1 behavior: queue eligibility comes from the sheet, the Slack thread timestamp identifies the property, `done` triggers saving, existing Cloudinary URLs are preserved, and the same row is updated. The new repository documents this behavior but does not claim production Slack file retrieval or Cloudinary-worker deployment as live until runtime acceptance tests pass.

## Verification implementation boundary

The legacy `verify_session.py` collects missing property fields in Slack, writes corrections to the same row, reapplies deterministic dependencies, validates, and only then changes the row state. No society profile/learning table is created.

## Explicit exclusions

Legacy society approval commands and workflows are obsolete and are not part of this map or the new repository. Legacy runtime bug/crash reporting is also excluded from the target Slack capability.
