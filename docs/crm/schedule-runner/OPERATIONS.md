# Schedule Runner Operations

## One-time setup

Configure the GitHub Actions repository secret:

`CRM_SOURCE_AUDIT_TOKEN`

Its value must exactly match the production Render environment variable used by the MCP adapter.

No token value belongs in repository files.

## Verification sequence

1. Confirm Render `/health` returns HTTP 200 and `{"ok":true}`.
2. Confirm Render startup reports the MCP adapter enabled and its audit token present.
3. Run the GitHub Actions workflow manually with `workflow_dispatch`.
4. Confirm the workflow exits successfully and prints the source-audit JSON.
5. Confirm the JSON contains successful WhAPI, Google Sheet and CRM persistence results.
6. Confirm the workflow is subsequently running on its hourly schedule.

## Security requirements

- Keep the workflow permission set read-only.
- Keep the MCP adapter read-only.
- Do not put credentials in workflow YAML, scripts, logs, query parameters or committed documentation.
- Do not broaden the MCP tool list to include send/write/deployment operations.
- Do not reuse the deterministic scheduler secret or any WhAPI API token as the MCP audit token.

## Evidence

For each production change, record the workflow commit SHA and the corresponding successful workflow run.

The schedule runner is independent of ChatGPT's ability to inject arbitrary authorization headers into a scheduled request. GitHub Actions owns the recurring execution and secret injection; Render owns the source adapters and production data access.
