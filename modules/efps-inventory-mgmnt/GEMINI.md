# Inventory Management — Agent Guidance

This module owns EFPS property inventory business logic.

## Phase 1 boundary
Implement only: dedicated two-number WhAPI intake, explicit `NEW`→`NEW` sessions, raw text capture, deterministic extraction, safe normalization, shared Google Maps resolution, validation, AI verification, and wording-only AI beautification.

Images may be recognized/countable but must not be downloaded in Phase 1. Do not implement Phase-2 media, lifecycle/locking, duplicate governance, downstream publishing, or Slack runtime.

## Source of truth
The canonical 48-column sheet contract is `shared/google_sheets/schema.py`. Deterministic extraction reads only `raw_message_text`; existing canonical row values are never extraction input.

## Shared boundary
Use `shared/google_maps` for Maps technical operations and `shared/google_sheets` for Sheets access. Do not duplicate either capability inside this module.

## Safety
Do not invent missing property facts, silently change business rules, overwrite downstream-owned AK:AO, or commit credentials. Runtime-unverified state must remain explicitly unverified.
