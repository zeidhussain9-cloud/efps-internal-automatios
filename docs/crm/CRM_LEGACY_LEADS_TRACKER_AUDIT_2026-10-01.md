# Legacy Leads Tracker runtime audit — 2026-10-01

## Target

Spreadsheet ID: `1GfM9lPQSukVpxCEVUlUDxFj_WYg0xQj8Inn7FA4sLVI`

Historical title: `Leads Tracker`

## Evidence checked

1. Repository-wide exact-ID search.
2. Current `crm-ui-dashboard` tracked-file search.
3. Executable Google Sheets/gspread/open-by-key reference search.
4. Current CRM Sheet contract in `shared/google_sheets/schema.py`.
5. Local legacy configuration reference.
6. Current Render service configuration and recent logs.
7. Direct read-only metadata access using the existing service account, without modifying the workbook.

## Findings

- The exact legacy spreadsheet ID is present in the historical extraction audit and legacy configuration evidence, not in the current CRM executable source.
- `leads_automation/google_sheet_config.txt` still contains the legacy ID, but no current executable repository reference to that config file was found.
- Historical `sync_to_sheet_v2.py` references remain in extraction evidence/logs; the script is not part of the current CRM runtime path.
- Current CRM inventory code uses `HOUSING_SHEET_ID`/`SHEET_ID` and `HOUSING_SHEET_TAB`; the canonical repository contract is `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc` / `Housing_Listings`.
- Direct metadata access confirms the legacy workbook remains accessible to the legacy service account. It currently exposes `Leads`, `Conversations`, `Events`, `Extraction Log`, and `Priority Sharing` tabs.
- Render log search for the exact legacy spreadsheet ID returned no hits for the available seven-day log window.

## Conclusion

The legacy Leads Tracker is **historical/documentation infrastructure, not an active dependency of the current CRM dashboard runtime**. Do not delete or alter it solely on this audit. It should remain available as historical evidence until any separate retention/archive decision is made.

The current production lead path is WhAPI → `crm_webhook_events` → Supabase CRM tables. The current inventory path is the separate `Housing_Listings` spreadsheet → inventory adapter/sync → `crm_inventory_snapshot`.