# Slack Command Surface

Canonical command surface for EFPS Inventory Management. There is one Slack slash command: `/efps`. Slack registers only that command; EFPS routes subcommands internally.

## Inventory channel — `#eps-wapi-pannel`

| Command | Purpose |
|---|---|
| `/efps help` | Show command help. |
| `/efps status` | Show pipeline stage counts (Raw, Processed, Catalogue Ready, Published, Rented Out). |
| `/efps run` | Force-run the WhatsApp lead ingestion worker. |
| `/efps show <listing_id>` | Display selected canonical property fields and row link. |
| `/efps add-property` | Start a new property entry session in a thread. |
| `/efps photos start` | Start the no-photo property queue. |
| `/efps catalogue start` | Start Meta catalogue creation for ready properties. |
| `/efps catalogue update` | Delete catalogues for rented-out properties. |
| `/efps assign <listing_id>` | Retry collection assignment for a property. |

## Lead channel — `#efps-leads`

No lead-specific slash command is required by the migrated implementation. Lead cards are updated through Slack Block Kit interactions and threads.

## Session thread controls

Sessions run in threads. Start from the channel view with a slash command, then use plain words in the thread. Commands are only recognized when they appear as standalone words, not within sentences.

### Property entry (`/efps add-property`)
- `done` — complete entry and process the property
- `cancel` — abandon the session

### Photo sessions (`/efps photos start`)
- `done` — save photos and move to next property
- `skip` — skip current property
- `exit` — close the session

### Catalogue sessions (`/efps catalogue start` or `update`)
- `go` — start processing (catalogue start)
- `yes` — confirm deletion (catalogue update)
- `no` / `exit` — cancel the operation
- `skip` — skip current property (catalogue start only)

## Removed / forbidden commands

The following are **not part of the current implementation**:

- `/efps fix <listing_id> <field> <value>` — removed; use Sheet editing or future admin tools
- `/efps verify start|next|skip|exit|submit` — removed; verification workflow removed
- `/efps pause` / `/efps resume` — batch control removed
- `/efps approve` — never implemented in new repository
- `/efps societies` / `/efps society <name>` — obsolete society approval queue
- `/efps bug *` — bug tracking commands not in current scope

The legacy source contained contradictory workflows. Commands listed here are obsolete and intentionally excluded.

