# EFPS Slack App Manifest

This is the cleaned target manifest specification migrated from the legacy `efps-platform` implementation.

## Important migration rule

The legacy manifest contains obsolete society commands/workflows in its prose. They are intentionally removed here. Do not reintroduce `/efps societies`, `/efps society`, society approval cards, or a society approval queue.

## Recorded legacy app identity

- App: `EFPS Wapi Pannel`
- App ID: `A0BTQGLKR4Z`
- Workspace: `Easyfind Automation Updates` (`T0BNK5NCZL1`)
- Bot display name: `efps_intake`
- Bot user: `U0BTLM3BXB8`
- Bot ID: `B0BT78HLSB1`

## Target manifest shape

```yaml
display_information:
  name: EFPS Wapi Pannel
  description: Property intake and lead tracking for EasyFind.
  background_color: "#1f2d3d"
  long_description: >-
    The operational control panel for EasyFind property intake, verification,
    photo collection, and lead operations.

features:
  bot_user:
    display_name: efps_intake
    always_online: true

  slash_commands:
    - command: /efps
      url: <NEW_REPOSITORY_SLASH_COMMAND_ENDPOINT>
      description: EasyFind operations panel
      usage_hint: status | run | show | fix | verify | photos | pause
      should_escape: false

oauth_config:
  scopes:
    bot:
      - commands
      - chat:write
      - files:read
      - channels:history
      - groups:history
      - channels:read
      - users:read
      - reactions:write
      - pins:write

settings:
  event_subscriptions:
    request_url: <NEW_REPOSITORY_EVENT_ENDPOINT>
    bot_events:
      - message.channels
      - message.groups
      - file_shared

  interactivity:
    is_enabled: true
    request_url: <NEW_REPOSITORY_INTERACTIVITY_ENDPOINT>

  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

## Scope purpose

| Scope | Purpose |
|---|---|
| `commands` | Receive `/efps`. |
| `chat:write` | Reports, property messages and lead cards. |
| `files:read` | Read Slack-attached photos for the photo workflow. |
| `channels:history` | Read public-channel thread replies. |
| `groups:history` | Read replies when applicable in private channels. |
| `channels:read` | Resolve/read channel metadata. |
| `users:read` | Associate commands with Slack users. |
| `reactions:write` | Operational acknowledgement reactions where used. |
| `pins:write` | Maintain the lead dashboard pin where used. |

## Event/interactivity requirements

`message.channels` and `message.groups` are required for session-thread replies in channels where the bot is a member. `file_shared` supports the photo collection event path.

Interactivity is required for lead-card buttons and other Block Kit actions.

## Installation procedure

When the new runtime endpoints are known:

1. Replace only the endpoint placeholders.
2. Save the manifest in the Slack app configuration.
3. Reinstall to the workspace when scopes/settings changed.
4. Ensure the bot is a member of all required operational channels.
5. Verify `/efps status`.
6. Verify a controlled thread reply and, separately, a controlled file/photo event.

Never put the bot token or signing secret in this file.

## Runtime verification status

The legacy repository recorded successful Slack API authentication and a message-post check on 2026-08-30. That is historical evidence only. The new repository's runtime endpoints and installation state are not verified by this document.
