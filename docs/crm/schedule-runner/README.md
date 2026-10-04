# CRM Source Audit Schedule Runner

## Purpose

This runner provides the permanent scheduled execution path for the production CRM source audit.

It invokes the existing production read-only MCP adapter and requests only:

- WhAPI channel/recent-source reconciliation
- canonical Google Housing Sheet snapshot
- CRM/Supabase persistence snapshot

The runner performs no CRM writes, WhAPI sends, Sheet writes, classification changes, AI execution, or deployment actions.

## Runtime

- Repository: `zeidhussain9-cloud/efps-internal-automatios`
- Production branch: `crm-ui-dashboard`
- Production service: `https://easyfind-crm-d01-d05.onrender.com`
- MCP endpoint: `POST /mcp`
- Schedule: hourly at minute 7
- Manual execution: GitHub Actions `workflow_dispatch`

The workflow is repository-owned at:

`.github/workflows/crm-source-audit-schedule.yml`

The executable runner is:

`scripts/crm-source-audit-runner.mjs`

## Authentication

The workflow supplies `CRM_SOURCE_AUDIT_TOKEN` from the GitHub Actions repository secret of the same name.

The secret is never committed, logged, or passed as a URL parameter.

The production MCP endpoint remains fail-closed when its audit token is absent or invalid.

## Failure semantics

The runner exits non-zero when:

- the token is missing
- the MCP endpoint is not HTTPS
- the MCP request fails
- MCP initialization fails
- the source-audit tool returns an error
- the source-audit payload is empty or invalid
- any source layer reports an embedded error

A successful run emits a compact JSON evidence payload to the workflow log.

## Scope boundary

This is an audit/evidence runner, not a CRM scheduler.

It does not reactivate the paused recurring AI scheduler and does not replace the deterministic classification scheduler, inventory sync, or WhAPI webhook runtime.
