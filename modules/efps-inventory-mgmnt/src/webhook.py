"""Compatibility entry point for the canonical Inventory Stage-1 runtime.

The live path is implemented by ``inventory_runtime``. This module remains as
an import-compatible wrapper for older callers and deliberately has no direct
Google Sheets column access.
"""
from __future__ import annotations

try:
    from .inventory_runtime import handle as _runtime_handle
except ImportError:
    from inventory_runtime import handle as _runtime_handle


def handle(message, *, sheets_client=None, store=None):
    """Delegate Inventory webhook handling to the canonical runtime."""
    return _runtime_handle(message, store=store, client=sheets_client)
