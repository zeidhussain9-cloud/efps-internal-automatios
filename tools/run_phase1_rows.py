"""Run only the deterministic Phase-1 inventory boundary for a sheet row range."""
from __future__ import annotations

import argparse
import json

from shared.google_sheets.client import GoogleSheetsClient
from src.batch import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-row", type=int, default=2)
    parser.add_argument("--end-row", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    client = GoogleSheetsClient()
    result = run(client, start_row=args.start_row, end_row=args.end_row, limit=args.limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result.get("write_failed") or result.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
