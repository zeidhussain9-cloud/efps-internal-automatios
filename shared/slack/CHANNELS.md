# Slack Channels and Routing

## Workspace

**Easyfind Automation Updates** — `T0BNK5NCZL1`

## Current operational channels

| Channel | ID | Role |
|---|---|---|
| `#eps-wapi-pannel` | `C0BTQGG8VT3` | Inventory panel: batch reports, property commands, photo sessions. |
| `#efps-leads` | `C0BTM6PH55L` | Lead cards, lead threads and the live lead dashboard. |
| `#eps-runtime-error-bugs-reporting` | `C0BUHV01L8Y` | Runtime and manual bug reporting. |
| `#epf-prop-aprovals` | `C0BUHUHRK0Q` | Property human-verification session channel. The historical name remains; this is not a society-approval channel. |

## Historical channels

Recorded in the legacy infrastructure documentation:

- `#sheet-entry` — `C0BRYFANB4Z`
- `#property-intake` — `C0BSAMSG4FM`
- `#housing-agent` — `C0BRXGCSS6A`
- `#meta-catalouge-bot` — `C0BSG4CHADC`

These are historical references, not automatically active destinations.

## Legacy app identity

- App: `EFPS Wapi Pannel` — `A0BTQGLKR4Z`
- Bot user: `efps_intake` — `U0BTLM3BXB8`
- Bot ID: `B0BT78HLSB1`
- Older app recorded: `Scout Sheet Bot` — `A0BR37G08CF`

## Routing rules

### Inventory panel

Batch summaries, `/efps status`, `/efps run`, `/efps show`, `/efps fix`, photo sessions, and pause/resume operations belong here.

### Property verification

Human verification sessions belong in `#epf-prop-aprovals`. The channel name is legacy terminology; its current purpose is property verification only.

### Leads

Lead cards are persistent Slack messages. Updates should edit the existing card where possible rather than creating a new card for every change. Lead interaction belongs in the lead thread.

### Runtime bugs

Manual and automatic bug reporting belongs in `#eps-runtime-error-bugs-reporting`. Slack-facing handlers should return HTTP 200 after filing an internal error so Slack does not generate retry storms.

## Channel membership

The bot must be a member of every channel where it needs to receive thread/event messages. In particular, photo and verification thread workflows depend on event delivery for channels in which the bot participates.

## Verification

The IDs above originate from the legacy repository and its recorded live checks. Before production activation in the new repository, verify bot membership, channel accessibility, API authentication, and message posting against the actual workspace.
