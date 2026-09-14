# Slack Implementation Map

## Legacy source → new shared capability

| Legacy area | New shared location / owner | Notes |
|---|---|---|
| Slack Web API `notify.py` | `shared/slack/client.py` | Reusable transport; modules choose content. |
| Slack request signing | `shared/slack/security.py` | HMAC verification and replay-age check. |
| Slack-safe customer text | `shared/slack/safety.py` | Prevent accidental mentions. |
| Channel IDs/config | `shared/slack/routing.py` | Destinations only. |
| `/efps` command routing | Owning module | Shared Slack does not contain inventory business rules. |
| `photo_session.py` | Inventory module + `shared/slack` transport | Session/business state belongs to inventory; Slack supplies transport. |
| `verify_session.py` | Inventory module + `shared/slack` transport | Verification rules belong to inventory. |
| `lead_card.py` / `digest.py` | Lead-management module + `shared/slack` transport | Lead business state remains in lead module. |
| `bugs.py` / `crash_report.py` | Owning runtime/error capability + `shared/slack` transport | Slack is notification/control surface, not bug database. |
| Slack manifest | `shared/slack/SLACK_APP_MANIFEST.md` | Cleaned; obsolete society workflow removed. |
| Operational command docs | `shared/slack/COMMANDS.md` | Canonical command surface. |
| Photo runbook | `shared/slack/REVERIFY_PHOTOS.md` | Current temporary bulk-photo process. |
| Verification runbook | `shared/slack/PROPERTY_VERIFICATION.md` | Property verification only. |

## Explicitly not migrated as business logic

- Society approval queue/cards.
- `/efps societies`.
- `/efps society <name>`.
- `/efps approve`.
- Legacy Lambda names/URLs as if they were new production endpoints.
- Secret values.

## Generic agent skills

The old repository also contained generic Slack agent skills for Block Kit, app creation, API use, CLI, docs, messaging, search and testing. Those are developer tooling guidance, not EFPS runtime behavior. The new shared capability should consume equivalent official Slack knowledge when implementing features; it should not copy unrelated generic skill text into the runtime package.
