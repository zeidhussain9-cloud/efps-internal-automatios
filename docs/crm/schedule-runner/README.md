# CRM Source Audit Schedule Runner

## Purpose

This runner provides the repository-owned scheduled execution path for the production CRM source audit.

It invokes the existing production read-only MCP adapter and requests only:

- WhAPI source reconciliation
- canonical Google Housing Sheet snapshot
- CRM/Supabase persistence snapshot

The runner performs no CRM writes, WhAPI sends, Sheet writes, classification changes, AI execution, or deployment actions.

## Runtime

- Repository: `zeidhussain9-cloud/efps-internal-automatios`
- Workflow: `.github/workflows/crm-source-audit-schedule.yml`
- Production branch definition: `crm-ui-dashboard`
- Production service: `https://easyfind-crm-d01-d05.onrender.com`
- MCP endpoint: `POST /mcp`
- Schedule: hourly at minute 7
- Manual execution: GitHub Actions `workflow_dispatch`

## Authentication

The scheduled workflow uses a short-lived GitHub Actions OIDC token with audience `efps-crm-source-audit`.

The production MCP adapter validates:

- GitHub OIDC issuer
- audience
- exact repository
- exact `main` workflow ref
- public repository visibility
- branch ref
- token time bounds
- GitHub signing key

The existing `CRM_SOURCE_AUDIT_TOKEN` remains supported for authorized non-GitHub MCP clients. The schedule runner does not require a new static GitHub secret.

## Failure semantics

The runner exits non-zero when:

- the authentication token is missing
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
