"""Repository-wide tracked-file audit for Inventory Phase 1."""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from shared.google_sheets import schema
STALE_TERMS=("declared " + "Standalone fallback","declared `" + "Standalone` fallback","fallback is " + "Standalone","fallback is `" + "Standalone`","fallback is **" + "Standalone**")
RESERVED_ALLOWED_FILES={
    "shared/google_sheets/schema.py",
    "shared/google_sheets/client.py",
    "modules/efps-inventory-mgmnt/src/validate.py",
    "tools/repository_audit.py",
}

def tracked_files()->list[Path]:
    result=subprocess.run(["git","ls-files","-z"],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    names=[name for name in result.stdout.decode("utf-8").split("\x00") if name];return [ROOT/name for name in names]
def is_binary(data:bytes)->bool:return b"\x00" in data[:8192]
def physical_line_count(text:str)->int:return len(text.splitlines()) if text else 0

def reserved_operation_hits(files:list[Path])->list[str]:
    hits=[]
    for path in files:
        rel=path.relative_to(ROOT).as_posix()
        if path.suffix != ".py" or rel in RESERVED_ALLOWED_FILES or "/test" in rel or path.name.startswith("test_"):
            continue
        text=path.read_text(encoding="utf-8")
        if "source_group" in text or "inventory_locked" in text:
            hits.append(f"{rel}: reserved field reference")
        if re.search(r"(?:A2|A\{[^}]+\}|[A-Z]\d+):AV", text) or ":AV\"" in text or ":AV'" in text:
            hits.append(f"{rel}: AV range reference")
    return hits

def audit()->int:
    files=tracked_files();folder_lines:defaultdict[str,int]=defaultdict(int);total_text_lines=text_files=binary_files=0;stale_hits=[]
    print("EFPS REPOSITORY LINE-BY-LINE AUDIT");print(f"ROOT: {ROOT}");print("SCOPE: git-tracked files only");print(f"FILES DISCOVERED: {len(files)}")
    for path in files:
        rel=path.relative_to(ROOT).as_posix();data=path.read_bytes()
        if is_binary(data):binary_files+=1;print(f"FILE {rel} | BINARY | lines=NA");continue
        text=data.decode("utf-8");lines=physical_line_count(text);text_files+=1;total_text_lines+=lines;parts=Path(rel).parts
        for i in range(1,len(parts)):folder_lines[Path(*parts[:i]).as_posix()]+=lines
        for term in STALE_TERMS:
            for number,line in enumerate(text.splitlines(),1):
                if term in line:stale_hits.append(f"{rel}:{number}: {line.strip()}")
        print(f"FILE {rel} | lines={lines}")
    print("\nFOLDER LINE TOTALS");print(f"FOLDER . | lines={total_text_lines}")
    for folder in sorted(folder_lines):print(f"FOLDER {folder} | lines={folder_lines[folder]}")
    print("\nCONTRACT INVARIANTS")
    schema_text=(ROOT/"shared/google_sheets/schema.py").read_text(encoding="utf-8");gate_text=(ROOT/"tools/production_projection_gate.py").read_text(encoding="utf-8");inventory_readme=(ROOT/"modules/efps-inventory-mgmnt/README.md").read_text(encoding="utf-8")
    reserved_hits=reserved_operation_hits(files)
    checks={
        "exact live bachelor tuple":schema.BY_NAME["bachelor_preference"].allowed_values==("Female Only ","Male Only","Open for both"),
        "trimmed bachelor value excluded":"Female Only" not in schema.BY_NAME["bachelor_preference"].allowed_values,
        "gate derives bachelor vocabulary from schema":'bachelor_allowed = set(schema.BY_NAME["bachelor_preference"].allowed_values)' in gate_text,
        "gate compares bachelor exactly":'if bachelor not in bachelor_allowed:' in gate_text,
        "gate compares tenant exactly":'if tenant not in tenant_allowed:' in gate_text,
        "landmark declares locality fallback dependency":re.search(r'\("landmark",PANEL,STAGE_2,\(\),\("locality",\)',schema_text) is not None,
        "inventory README has no stale Standalone fallback":all(term not in inventory_readme for term in STALE_TERMS),
        "reserved columns are exact":schema.RESERVED_COLUMNS==("source_group","inventory_locked"),
        "reserved columns have no operational owner":all(schema.owner_of(name)==schema.RESERVED and schema.BY_NAME[name].stage==schema.RESERVED_STAGE for name in schema.RESERVED_COLUMNS),
        "reserved columns are not panel-writable":all(name not in schema.writable_by(schema.PANEL) for name in schema.RESERVED_COLUMNS),
        "no operational reserved-column references":not reserved_hits,
        "V10 subtype vocabulary is exact":schema.BY_NAME["property_subtype"].allowed_values==("Apartment","Villa","Independent House","Duplex","Studio","Independent Floor"),
    }
    failures=[name for name,ok in checks.items() if not ok]
    for name,ok in checks.items():print(f"CHECK {name}: {'PASS' if ok else 'FAIL'}")
    for hit in reserved_hits:print(f"RESERVED OPERATION {hit}")
    print("\nAUDIT SUMMARY");print(f"TEXT FILES READ: {text_files}");print(f"BINARY FILES: {binary_files}");print(f"TEXT LINES READ: {total_text_lines}");print(f"STALE HITS: {len(stale_hits)}")
    for hit in stale_hits:print(f"STALE {hit}")
    if stale_hits or failures:print("REPOSITORY AUDIT: FAIL");return 1
    print("REPOSITORY AUDIT: PASS");return 0
if __name__=="__main__":raise SystemExit(audit())
