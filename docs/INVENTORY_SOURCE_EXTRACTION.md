# Inventory Source Extraction Contract

**Status:** Active

## Purpose

This document is the canonical contract for deterministic extraction from `raw_message_text` in Inventory Management Stage 2. It exists to prevent repeated field-specific fixes that only handle one raw-message representation.

## Source-of-truth rule

`raw_message_text` is the authoritative Stage-2 source. Existing Stage-2 Sheet values are not used as evidence to manufacture a new extraction result. Explicit source facts outrank inferred defaults.

## Canonical processing boundary

All deterministic labelled-field extraction must first respect WhatsApp source-message boundaries. The shared module `modules/efps-inventory-mgmnt/src/source_segments.py` is the canonical boundary parser.

Supported transport forms include bracketed timestamps, ISO-like timestamps, slash-date timestamps, newline-delimited messages, and inline pipe-delimited timestamped messages. A field value must never consume content from a later source message.

## Extraction contract

1. Segment the raw source into source-message units.
2. Extract a labelled field from one source unit at a time.
3. Normalize the extracted source value without inventing facts.
4. Apply business rules only after source extraction.
5. Use Maps only for the documented Stage-2 enrichment/verification step.
6. Treat unresolved ambiguity as a validation/runtime state rather than silently changing source facts.

## Property-type precedence

For `internal_property_type`, explicit labelled source evidence is authoritative. Boolean forms such as `Gated Community: Yes` and `Semi Gated: Yes` are explicit evidence. Explicit negative boolean forms do not classify the property as gated. Canonical free-text phrases are evaluated within an individual source unit only.

## Field-specific safeguards

- Society, landmark, locality, property subtype, highlights, age, tenant preference, bachelor preference, pet status, servant-room status, and maintenance labelled values are extracted within source units.
- Placeholder-only source values are treated as blank by normalization.
- Mixed maintenance values such as `2777 + Water` remain source facts; normalization does not silently discard the suffix.
- Existing furnishing, tenant, parking, pet, amenity, subtype, title, and highlight business rules remain downstream normalization rules rather than extraction shortcuts.

## Regression requirement

Every production extraction fix must include a regression fixture representing the source-message shape that caused the failure. A fix is not complete if it only makes the current 25-row projection look correct. The test must prove that the same source-boundary rule remains correct for future inventory sessions.

## Model-test interpretation

The read-only 25-row model test compares the Stage-2 projection with the persisted Sheet. Blank Sheet Stage-2 cells are expected differences before persistence and are not extraction failures. Populated Sheet values that conflict with a source-grounded projection require source inspection before being labelled a bug.

The test must report these categories separately: expected blank-cell projection differences, populated-cell conflicts, formatting-only differences, and Maps verification issues.
