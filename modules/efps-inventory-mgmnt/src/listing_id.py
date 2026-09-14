"""Immutable EF-YYMM-XXXX inventory IDs, migrated from the legacy contract."""
from __future__ import annotations
from datetime import datetime, timezone
import secrets, re
ALPHABET="0123456789ABCDEFGHJKMNPQRSTVWXYZ"
PATTERN=re.compile(r"^EF-\d{4}-["+ALPHABET+r"]{4}$")
def generate(existing=(), now:datetime|None=None)->str:
    now=now or datetime.now(timezone.utc); taken={str(x).upper() for x in existing if x}
    prefix=f"EF-{now:%y%m}-"
    for _ in range(100):
        x=prefix+''.join(secrets.choice(ALPHABET) for _ in range(4))
        if x not in taken:return x
    raise RuntimeError("Unable to issue unique listing ID")
def is_valid(value:str)->bool:return bool(PATTERN.fullmatch(value or ""))
