#!/usr/bin/env python3
"""Read-only, single-source lead export. No database writes or network calls."""
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path

SOURCE = "+919148338801"
COLUMNS = (
    "phone_number", "customer_name", "lead_status", "priority",
    "current_requirement", "bhk_requirement", "preferred_location",
    "budget_min", "budget_max", "furnishing_preference", "occupancy_type",
    "pet_preference", "parking_required", "move_in_date", "last_interaction_date",
    "next_followup_date", "followup_count", "tags", "notes", "created_at",
    "updated_at", "extracted_from_phone", "classification"
)

def prepare(db_path, output_path):
    db_path = Path(db_path).resolve()
    output_path = Path(output_path).resolve()
    if output_path.is_relative_to(db_path.parent / "crm-ui-dashboard"):
        raise ValueError("Private exports must remain outside the Git worktree")
    if output_path.exists():
        raise FileExistsError("Refusing to overwrite a previous export")
    connection = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in connection.execute(
            "SELECT " + ",".join(COLUMNS) + " FROM leads "
            "WHERE extracted_from_phone=? ORDER BY phone_number", (SOURCE,))]
        if len(rows) != 228 or len({r["phone_number"] for r in rows}) != len(rows):
            raise ValueError("Source lead count/identity differs from audited 228")
        if any(not r["phone_number"] or r["phone_number"] == SOURCE for r in rows):
            raise ValueError("Invalid customer identity or business self-contact")
        if any(r["extracted_from_phone"] != SOURCE for r in rows):
            raise ValueError("Cross-source row detected")
        data = json.dumps({"source_number": SOURCE, "leads": rows},
                          ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        output_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return {"source_number": SOURCE, "lead_count": len(rows),
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                "database_writes": 0}
    finally:
        connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.db, args.output)))
