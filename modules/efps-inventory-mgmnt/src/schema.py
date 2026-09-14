"""Inventory view of the canonical sheet schema.

This is intentionally not a second schema. All physical fields, ownership,
stages, allowed values, and dependencies come from shared.google_sheets.schema.
"""
from shared.google_sheets.schema import *
from shared.google_sheets.schema import COLUMNS,NAMES,BY_NAME,CONTRACT_NAMES,EXTRA_NAMES,TAIL_NAMES,stage_of,owner_of,letter
