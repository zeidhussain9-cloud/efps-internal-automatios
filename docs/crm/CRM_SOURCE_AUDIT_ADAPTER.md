# CRM Source Audit Adapter

## Purpose

The production CRM exposes a read-only MCP adapter for independent source verification. It does not replace the WhAPI webhook path or the Google Sheet inventory reconciliation path.

## Sources

- WhAPI channel for +919148338801
- Canonical Google Sheet 1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc, worksheet Housing_Listings
- Supabase CRM persistence

## MCP endpoint

Production CRM service exposes the MCP endpoint at:

POST /mcp

The endpoint is stateless Streamable HTTP and requires:

Authorization: Bearer <CRM_SOURCE_AUDIT_TOKEN>

The server exposes only read-only tools:

- whapi_channel_health
- whapi_recent_messages
- whapi_message
- google_housing_sheet_snapshot
- crm_source_audit_snapshot

No message send, contact mutation, Sheet write, lead write, classification write, or deployment action is exposed.

## Cross-source audit

crm_source_audit_snapshot reads all three layers without modifying them and returns:

- WhAPI recent inbound message count and latest provider timestamp
- Google Sheet row/column snapshot
- CRM webhook total/latest/error count
- CRM message total/latest
- latest Housing Sheet sync row count/timestamp

CRM SQL runs inside a read-only transaction.

## Runtime configuration

Required:

- WHAPI_API_TOKEN
- GOOGLE_SERVICE_ACCOUNT_JSON_BASE64, GOOGLE_SERVICE_ACCOUNT_JSON, or GOOGLE_APPLICATION_CREDENTIALS
- HOUSING_SHEET_ID or SHEET_ID
- HOUSING_SHEET_TAB
- DATABASE_URL
- CRM_SOURCE_AUDIT_MCP_ENABLED=true
- CRM_SOURCE_AUDIT_TOKEN

The Google Sheet adapter uses the existing read-only Sheets scope and canonical inventory adapter. Secrets are never logged.

## Security boundary

The adapter is deliberately narrower than the full WhAPI MCP. WhAPI's official MCP exposes broad WhatsApp capabilities; this CRM adapter exposes only the read operations needed for source reconciliation.

The adapter is an audit/evidence layer. The existing webhook, deterministic scheduler, inventory scheduler, and Supabase persistence remain authoritative runtime paths.

## Verification

Repository test coverage includes MCP protocol/authentication and confirms the exposed tool list contains only the read-only audit tools.

Production verification must separately establish:

1. Render startup reports the WhAPI token, Sheet credential/ID, MCP enable flag and audit token as present.
2. The deployed /mcp endpoint accepts the configured bearer token.
3. WhAPI read calls succeed.
4. Google Sheet read succeeds.
5. CRM read-only reconciliation succeeds.
6. No production write path is reachable through the adapter.
