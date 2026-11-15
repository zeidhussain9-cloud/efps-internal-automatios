#!/usr/bin/env python3
"""Assemble the isolated, minimal Notion intake Lambda source package."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".aws-sam" / "notion-source"
if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir(parents=True)

src = ROOT / "modules" / "efps-inventory-mgmnt" / "src"
for file in src.glob("*.py"):
    if file.name.startswith("test_"):
        continue
    shutil.copy2(file, DEST / file.name)

shared_dest = DEST / "shared"
shared_dest.mkdir()
for name in ("__init__.py", "credentials.py"):
    source = ROOT / "shared" / name
    if source.exists():
        shutil.copy2(source, shared_dest / name)
for package in ("cloudinary", "ola_maps"):
    shutil.copytree(ROOT / "shared" / package, shared_dest / package,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests", "test_*"))
# The inventory pipeline still uses the historical field schema as a pure data contract.
# Ship only that schema module, never the Sheets client or Google Sheets SDK.
sheets_schema = shared_dest / "google_sheets"
sheets_schema.mkdir()
(sheets_schema / "__init__.py").write_text("\"\"\"Legacy field schema only; no Google Sheets client is packaged.\"\"\"\n")
shutil.copy2(ROOT / "shared" / "google_sheets" / "schema.py", sheets_schema / "schema.py")

(DEST / "requirements.txt").write_text(
    "requests>=2.32,<3\n"
    "cloudinary>=1.41,<2\n"
    "google-auth>=2.35,<3\n"
)
print(f"Prepared isolated Notion Lambda package at {DEST}")
