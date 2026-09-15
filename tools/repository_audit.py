"""Repository-wide tracked-file audit for Inventory Phase 1.

The audit is read-only. It enumerates the exact Git-tracked repository files,
reports physical line counts for every UTF-8 text file, identifies binary files,
and fails on known stale contract statements or known contract drift.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STALE_TERMS = (
    "declared " + "Standalone fallback",
    "declared `" + "Standalone` fallback",
    "fallback is " + "Standalone",
    "fallback is `" + "Standalone`",
    "fallback is **" + "Standalone**",
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    names = [name for name in result.stdout.decode("utf-8").split("\x00") if name]
    return [ROOT / name for name in names]


def is_binary(data: bytes) -> bool:
    return b"\x00" in data[:8192]


def physical_line_count(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def audit() -> int:
    files = tracked_files()
    folder_lines: defaultdict[str, int] = defaultdict(int)
    total_text_lines = 0
    text_files = 0
    binary_files = 0
    stale_hits: list[str] = []

    print("EFPS REPOSITORY LINE-BY-LINE AUDIT")
    print(f"ROOT: {ROOT}")
    print("SCOPE: git-tracked files only")
    print(f"FILES DISCOVERED: {len(files)}")

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        if is_binary(data):
            binary_files += 1
            print(f"FILE {rel} | BINARY | lines=NA")
            continue

        text = data.decode("utf-8")
        lines = physical_line_count(text)
        text_files += 1
        total_text_lines += lines
        parts = Path(rel).parts
        for i in range(1, len(parts)):
            folder_lines[Path(*parts[:i]).as_posix()] += lines

        for term in STALE_TERMS:
            for number, line in enumerate(text.splitlines(), 1):
                if term in line:
                    stale_hits.append(f"{rel}:{number}: {line.strip()}")
        print(f"FILE {rel} | lines={lines}")

    print("\nFOLDER LINE TOTALS")
    print(f"FOLDER . | lines={total_text_lines}")
    for folder in sorted(folder_lines):
        print(f"FOLDER {folder} | lines={folder_lines[folder]}")

    print("\nCONTRACT INVARIANTS")
    schema_text = (ROOT / "shared/google_sheets/schema.py").read_text(encoding="utf-8")
    gate_text = (ROOT / "tools/production_projection_gate.py").read_text(encoding="utf-8")
    inventory_readme = (ROOT / "modules/efps-inventory-mgmnt/README.md").read_text(encoding="utf-8")
    bachelor_match = re.search(
        r'\("bachelor_preference",PANEL,STAGE_2,\((?:"Female Only ",\s*)"Male Only",\s*"Open for both"\)',
        schema_text,
    )
    checks = {
        "exact live bachelor tuple": bachelor_match is not None,
        "trimmed bachelor value excluded": '"Female Only" not in BY_NAME["bachelor_preference"].allowed_values' in schema_text,
        "gate derives bachelor vocabulary from schema": 'bachelor_allowed = set(schema.BY_NAME["bachelor_preference"].allowed_values)' in gate_text,
        "gate compares bachelor exactly": 'if bachelor not in bachelor_allowed:' in gate_text,
        "gate compares tenant exactly": 'if tenant not in tenant_allowed:' in gate_text,
        "landmark has no locality dependency": re.search(r'\("landmark",PANEL,STAGE_2,\(\),\(\),', schema_text) is not None,
        "inventory README has no stale Standalone fallback": all(term not in inventory_readme for term in STALE_TERMS),
    }
    failures = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"CHECK {name}: {'PASS' if ok else 'FAIL'}")

    print("\nAUDIT SUMMARY")
    print(f"TEXT FILES READ: {text_files}")
    print(f"BINARY FILES: {binary_files}")
    print(f"TEXT LINES READ: {total_text_lines}")
    print(f"STALE HITS: {len(stale_hits)}")
    for hit in stale_hits:
        print(f"STALE {hit}")

    if stale_hits or failures:
        print("REPOSITORY AUDIT: FAIL")
        return 1
    print("REPOSITORY AUDIT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(audit())
