# Inventory Management — Agent Guidance

This module owns EFPS property inventory business logic.

## Boundary

Use shared services for technical capabilities. Keep inventory decisions and inventory-specific rules here.

## Current status

Skeleton only. Do not add implementation until a concrete inventory capability is approved and its source truth is established.

## Naming

Keep the module name lowercase and hyphenated: `efps-inventory-mgmnt`.

## Safety

Do not invent missing property facts, silently change business rules, or commit credentials.