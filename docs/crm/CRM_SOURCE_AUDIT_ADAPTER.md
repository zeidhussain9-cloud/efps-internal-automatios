# CRM Source Audit Adapter

## Purpose

The production CRM exposes a read-only MCP adapter for independent source verification. It keeps the WhAPI read-only audit tools and reports inventory from the Notion-owned Supabase projection. It does not perform mutations.

## Sources

- WhAPI channel for +919148338801
- Notion Housing Listings mirrored to `public.crm_inventory_snapshot` with `source_kind='housing_notion'`
- Supabase CRM persistence

## MCP endpoint

The endpoint is `POST /mcp`, a stateless Streamable HTTP endpoint requiring:

`Authorization: Bearer <CRM_SOURCE_AUDIT_TOKEN>`

The server exposes only read-only tools:

- `whapi_channel_health`
- `whapi_recent_messages`
- `whapi_message`
- `notion_housing_inventory_snapshot`
- `crm_source_audit_snapshot`

No message send, contact mutation, inventory write, lead write, classification write, or deployment action is exposed.

## Cross-source audit

`crm_source_audit_snapshot` reads WhAPI, Notion inventory projection, and CRM state without modifying them. The inventory snapshot reports active Notion-owned rows, listing state, catalog fields, media URLs, and counts. CRM SQL runs inside a read-only transaction.

## Runtime configuration

Required values are `WHAPI_API_TOKEN`, `DATABASE_URL`, `CRM_SOURCE_AUDIT_MCP_ENABLED=true`, and `CRM_SOURCE_AUDIT_TOKEN`. The inventory audit queries the existing Supabase projection; it does not require Google Sheets credentials or a Sheet ID. Secrets are never logged.

## Security boundary

The adapter is deliberately narrower than the full WhAPI MCP and contains no inventory mutation path. The old Sheet reconciliation cron is disabled; the dashboard and audit use only active `housing_notion` rows.

## Current production verification

The production adapter was not live-verified as part of the Notion inventory migration. Existing production feature-flag and credential state must be checked separately before relying on the MCP endpoint. This does not affect dashboard inventory reads.

## Verification

Repository test coverage checks MCP authentication and verifies that exposed tools are read-only. Production verification separately establishes that the endpoint is enabled, bearer authorization works, WhAPI reads succeed, Supabase Notion inventory reads are complete, and no write path is reachable.
