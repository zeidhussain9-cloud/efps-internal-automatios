"""Authoritative community-level property-type adjudications.

This registry is intentionally explicit. A community name is not treated as
proof of gating merely because it is an apartment/society name. Entries are
added only when EFPS has an independently adjudicated property-type fact.
"""
from __future__ import annotations

import re

# Current production corpus adjudication.
# Prima Hi-Life is explicitly documented as an exclusive gated community by
# the project source and is also surfaced as a gated community by current
# rental inventory. This entry closes the otherwise ambiguous case where the
# incoming WhatsApp source contains the community name but no gating keyword.
KNOWN_COMMUNITY_PROPERTY_TYPES: dict[str, str] = {
    "prima hi life": "Gated Community",
    "prima hilife": "Gated Community",
    "prima hi-life": "Gated Community",
}


def normalize_community_name(value: str) -> str:
    value = str(value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def resolve_known_community_property_type(value: str) -> str:
    return KNOWN_COMMUNITY_PROPERTY_TYPES.get(normalize_community_name(value), "")
