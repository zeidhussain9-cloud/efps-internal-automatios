# Schedule Runner Operations

## Verification sequence

1. Confirm Render /health is healthy.
2. Confirm Render startup reports the MCP adapter enabled and the audit adapter credentials present.
3. Run the GitHub Actions workflow manually with workflow_dispatch.
4. Confirm the workflow exits successfully and prints the source-audit JSON.
5. Confirm the JSON contains successful WhAPI, Google Sheet, catalog and CRM persistence results.
6. Confirm Sheet available count equals WhAPI product count.
7. Confirm products-with-collections plus products-without-collections equals the WhAPI product count.
8. Confirm the workflow subsequently runs on its hourly schedule.

## Security requirements

- The scheduled workflow uses contents: read only; its verified credential is CRM_SOURCE_AUDIT_TOKEN.
- Keep the MCP adapter read-only.
- Do not put credentials in workflow YAML, scripts, logs or query parameters.
- Do not broaden the MCP tool list to include send/write/deployment operations.
- Do not reuse the deterministic scheduler secret or any WhAPI API token as the MCP audit token.

## Evidence

For each production change, record the workflow commit SHA and corresponding successful workflow run.

The schedule runner is independent of ChatGPT scheduled tasks. GitHub Actions owns the recurring execution; Render owns the source adapters and production data access.
