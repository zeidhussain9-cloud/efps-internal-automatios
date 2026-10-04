# CRM Source Audit Schedule Runner

## Purpose

Repository-owned scheduled execution path for the production CRM source audit.

Each run is read-only and reconciles:

- WhAPI channel/message source health
- canonical Google Housing Sheet inventory
- WhatsApp Business catalog products and collections
- CRM/Supabase persistence

Catalog reconciliation historically used the Sheet's available inventory count as the expected catalog count and read WhAPI products/collections. As of the 2026-10-05 safety hardening, direct WhAPI API access is policy-disabled and non-catalog operations are hard-blocked. Therefore no current scheduler run may claim live WhAPI catalog reconciliation unless an independently authorized catalog source is explicitly enabled and verified.

- Sheet available count
- WhAPI product count
- matched/mismatched state
- products assigned to at least one collection
- products with no collection assignment

The runner performs no CRM writes, WhAPI sends, Sheet writes, classification changes, AI execution, or deployment actions.

## Runtime

- Repository: zeidhussain9-cloud/efps-internal-automatios
- Workflow: .github/workflows/crm-source-audit-schedule.yml
- Production branch definition: crm-ui-dashboard
- Production service: https://easyfind-crm-d01-d05.onrender.com
- MCP endpoint: POST /mcp
- Schedule: hourly at minute 7 UTC
- Manual execution: GitHub Actions workflow_dispatch

## Authentication

The scheduled workflow uses the existing GitHub Actions secret CRM_SOURCE_AUDIT_TOKEN as a Bearer credential for the production read-only MCP endpoint.

The scheduled workflow uses the configured static audit secret because this is the verified working production path. The MCP endpoint remains fail-closed and authenticated.

No WhAPI API token is used as the MCP audit credential.

## Failure semantics

The runner exits non-zero when:

- the audit credential is missing
- the MCP endpoint is not HTTPS
- the MCP request or initialization fails
- the source-audit payload is empty or invalid
- any source layer reports an error
- the catalog reconciliation is incomplete
- Sheet available count does not equal the WhAPI product count
- the CRM requirement/matching audit is incomplete

A successful run emits compact JSON evidence including collection assignment counts and the Point 40–42 requirement/matching audit.

## Scope boundary

This is an audit/evidence runner, not a CRM scheduler.

It does not reactivate the paused recurring AI scheduler and does not replace the deterministic classification scheduler, inventory sync, or WhAPI webhook runtime.
