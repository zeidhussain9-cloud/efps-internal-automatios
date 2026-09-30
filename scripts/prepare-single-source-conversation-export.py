#!/usr/bin/env python3
"""Read-only export of the historical conversation archive for one WhatsApp source."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path

SOURCE = "+919148338801"
EXPECTED_LEADS = 228
EXPECTED_MESSAGES = 5286

def prepare(db_path: str, output_path: str) -> dict:
    db = Path(db_path).resolve()
    out = Path(output_path).resolve()
    if out.exists():
        raise FileExistsError("Refusing to overwrite a previous conversation export")
    connection = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        leads = [dict(r) for r in connection.execute(
            "SELECT phone_number FROM leads WHERE extracted_from_phone=? ORDER BY phone_number",
            (SOURCE,),
        )]
        phones = {row["phone_number"] for row in leads}
        if len(leads) != EXPECTED_LEADS or len(phones) != EXPECTED_LEADS:
            raise ValueError("Source lead identity/count differs from audited 228")
        rows = [dict(r) for r in connection.execute(
            """SELECT c.message_id, c.phone_number, c.direction, c.message_body,
                      c.message_type, c.media_urls, c.media_filenames, c.sender_name,
                      c.timestamp, c.replied_to_id, c.is_processed, c.extracted_intent,
                      c.extracted_entities, c.sentiment, c.requires_followup,
                      c.created_at, c.processed_at
               FROM conversations c
               JOIN leads l ON l.phone_number=c.phone_number
               WHERE l.extracted_from_phone=?
               ORDER BY c.timestamp, c.message_id""",
            (SOURCE,),
        )]
        if len(rows) != EXPECTED_MESSAGES:
            raise ValueError(f"Historical message count is {len(rows)}, expected {EXPECTED_MESSAGES}")
        if any(row["phone_number"] not in phones for row in rows):
            raise ValueError("Conversation row references a phone outside the 228-lead source")
        if len({row["message_id"] for row in rows}) != len(rows):
            raise ValueError("Duplicate SQLite message_id detected")
        payload = {
            "source_number": SOURCE,
            "lead_count": len(leads),
            "message_count": len(rows),
            "messages": rows,
            "provenance": {
                "source": "SQLite conversations joined to leads.extracted_from_phone",
                "provider_message_id": "not present in historical SQLite; source_message_id is the SQLite message_id",
            },
        }
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        out.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        return {
            "source_number": SOURCE,
            "lead_count": len(leads),
            "message_count": len(rows),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "database_writes": 0,
        }
    finally:
        connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.db, args.output)))
