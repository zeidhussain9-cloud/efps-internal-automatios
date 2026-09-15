"""Inventory webhook business flow.

Only text reaches inventory here. Property photos are intentionally handled by
Slack's manual thread workflow, not by the WhAPI inventory listener.
"""
from __future__ import annotations

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.whatsapp_whapi import config as whapi_config
from shared.whatsapp_whapi.webhook import IncomingMessage

from . import pipeline

FOLLOWUP_SEPARATOR = "\n--- follow-up ---\n"


def _field(message: IncomingMessage | dict, name: str, default=""):
    if isinstance(message, IncomingMessage):
        return getattr(message, name, default)
    return message.get(name, default)


def _is_new(text: str) -> bool:
    return str(text or "").strip().casefold() == "new"


def _find_open_row(client: GoogleSheetsClient, source_key: str):
    values = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, schema.full_range(2).replace("2:2", "2:1000"))
    for row_number, values_row in enumerate(values, start=2):
        if len(values_row) < schema.GRID_WIDTH:
            continue
        row = schema.row_to_mapping(values_row)
        if row.get("source_group") == source_key and not str(row.get("inventory_locked", "")).strip():
            if str(row.get("intake_status", "")).strip() == "Raw":
                return row_number, row
    return None, None


def _find_by_listing_id(client: GoogleSheetsClient, listing_id: str):
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:A")
    for row_number, row in enumerate(rows, start=2):
        if row and str(row[0]).strip() == listing_id:
            full = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, schema.full_range(row_number))
            if full:
                return row_number, schema.row_to_mapping(full[0])
            return row_number, None
    return None, None


def _lock(client: GoogleSheetsClient, row_number: int) -> None:
    client.write_range(schema.SHEET_ID, schema.WORKSHEET_NAME,
                       schema.range_for("inventory_locked", "inventory_locked", row_number), [["Yes"]])


def _append_text(row: dict, text: str, message_id: str, timestamp) -> None:
    text = str(text or "").strip()
    if not text:
        return
    marker = f"msg:{message_id}" if message_id else ""
    if marker and marker in str(row.get("raw_message_text", "")):
        return
    chunk = f"[{timestamp}]" if timestamp else ""
    chunk = f"{chunk} [{message_id}] {text}".strip() if message_id else f"{chunk} {text}".strip()
    existing = str(row.get("raw_message_text", "")).strip()
    row["raw_message_text"] = f"{existing}{FOLLOWUP_SEPARATOR}{chunk}" if existing else chunk
    row["intake_status"] = "Raw"


def _close_and_process(client: GoogleSheetsClient, row_number: int, row: dict) -> dict:
    raw_text = str(row.get("raw_message_text", ""))
    if not raw_text.strip():
        _lock(client, row_number)
        return {"state": "closed", "listing_id": row.get("listing_id", ""), "processed": False}

    processed, issues = pipeline.process_closed_session(raw_text, row=row)
    processed["inventory_locked"] = "Yes"
    pipeline.write_phase1_update(client, row_number, processed)
    _lock(client, row_number)
    return {"state": "closed", "listing_id": row.get("listing_id", ""), "processed": True, "issues": issues}


def handle(message: IncomingMessage | dict, *, sheets_client: GoogleSheetsClient | None = None) -> dict:
    """Apply NEW-to-NEW inventory boundaries using the sheet as durable state."""
    if not (message.is_inventory_listener if isinstance(message, IncomingMessage) else bool(message.get("is_inventory_listener"))):
        return {"state": "ignored"}
    if sheets_client is None:
        sheets_client = GoogleSheetsClient()

    chat_id = str(_field(message, "chat_id") or _field(message, "sender") or "").strip()
    sender = whapi_config.normalise_phone(str(_field(message, "sender") or chat_id))
    source_key = f"inventory:{sender or chat_id}"
    text = str(_field(message, "body") or "").strip()
    message_id = str(_field(message, "message_id") or "")
    timestamp = _field(message, "timestamp", "")

    row_number, row = _find_open_row(sheets_client, source_key)

    if _is_new(text):
        result = {"state": "opened", "closed": None}
        if row_number and row:
            result["closed"] = _close_and_process(sheets_client, row_number, row)
        listing_id = pipeline.next_listing_id(sheets_client)
        new_row = pipeline.initial_row(listing_id, source_group=source_key)
        pipeline.write_new_property(sheets_client, new_row)
        return {**result, "listing_id": listing_id}

    if not row_number or not row:
        return {"state": "ignored", "reason": "before first NEW"}

    if message_id and f"msg:{message_id}" in str(row.get("raw_message_text", "")):
        return {"state": "duplicate", "listing_id": row.get("listing_id", "")}

    _append_text(row, text, message_id, timestamp)
    if text:
        pipeline.write_phase1_update(sheets_client, row_number, pipeline.process_phase1(row["raw_message_text"], row=row).row)
    return {"state": "collecting", "listing_id": row.get("listing_id", "")}
