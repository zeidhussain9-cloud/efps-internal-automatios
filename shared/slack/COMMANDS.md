# Slack Command Surface

Canonical command surface migrated from the legacy EFPS panel. There is one Slack slash command: `/efps`. Slack registers only that command; EFPS routes subcommands internally.

## Inventory channel — `#eps-wapi-pannel`

| Command | Purpose |
|---|---|
| `/efps help` | Show command help. |
| `/efps status` | Show Raw/Processed/Needs Review counts, row count and batch state. |
| `/efps run` | Dispatch a batch run immediately unless batches are paused. |
| `/efps show <listing_id>` | Display selected canonical property fields and row link. |
| `/efps fix <listing_id> <field> <value>` | Apply one manual correction, re-run deterministic dependencies, validate, and write the same row. |
| `/efps photos start` | Start the no-photo property queue. |
| `/efps photos next` | Move to the next photo property. |
| `/efps photos skip` | Skip the current photo property for the session. |
| `/efps photos exit` | Close the photo session. |
| `/efps catalogue start` | Start Meta catalogue creation for ready properties. |
| `/efps pause` | Disable scheduled inventory batches. |
| `/efps resume` | Re-enable scheduled inventory batches. |

## Property verification channel — `#epf-prop-aprovals`

| Command/session control | Purpose |
|---|---|
| `/efps verify start` | Start the human verification queue for rows needing review. |
| `/efps verify next` | Move to the next verification item. |
| `/efps verify skip` | Skip the current item for the session. |
| `/efps verify exit` | Close the verification session. |
| `/efps verify submit` | Submit the current answers when invoked through the command surface. |
| bare `submit` in the property thread | Submit the current verification answers. |
| bare `next` / `skip` / `exit` | Session controls in the property thread. |

## Runtime bug channel — `#eps-runtime-error-bugs-reporting`

| Command | Purpose |
|---|---|
| `/efps bug report` | Start a guided bug report. |
| `/efps bug submit` | Submit the active bug interview. |
| `/efps bug cancel` | Cancel the active bug interview. |
| `/efps bug show <BUG-ID>` | Show one bug. |
| `/efps bug fix <BUG-ID> <note>` | Record the fix and close the bug. |
| `/efps bugs` | Flush unannounced failures and list open bugs. |

## Lead channel — `#efps-leads`

No lead-specific slash command is required by the migrated implementation. Lead cards are updated through Slack Block Kit interactions and threads.

## Photo thread controls

The slash command cannot be used inside a Slack thread. Start the session from the channel view, then use plain words in the session thread:

- `done` — dispatch photo save for the current property.
- `next` / `skip` — advance/pass according to session behavior.
- `exit` — close the session.

A sentence containing these words is not automatically a command; command matching must remain explicit.

## Catalogue thread controls

Similar to photo sessions, catalogue creation is thread-based:

- `go` — start creating catalogues for all ready properties, processing one by one with live updates.
- `skip` — skip the current property (catalogue session only).
- `exit` — close the catalogue session.

The system automatically advances to the next property after each successful creation. When all properties are processed, the session closes automatically.

## Ownership constraints for `/efps fix`

The legacy implementation explicitly blocks direct correction of:

- Maps-owned: `locality`, `city`, `pincode`, `google_maps_url`.
- System-owned: `listing_id`, `raw_message_text`, `intake_status`, `source_group`, `inventory_locked`.
- Downstream-owned: `posted_url`, `posted_at`, `meta_catalog_id`, `meta_catalog_status`.

Manual fixes must not bypass deterministic normalization or validation.

## Removed / forbidden commands

The following are **not part of the new repository**:

- `/efps approve`
- `/efps societies`
- `/efps society <name>`
- Any separate society approval queue/card/workflow.

The legacy source contained contradictory society-approval prose. It is obsolete and intentionally excluded.
