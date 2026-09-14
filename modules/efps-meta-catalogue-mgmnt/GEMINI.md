# Meta Catalogue Management — Agent Guidance

This module owns Meta / WhatsApp catalogue business logic.

## Boundary

The module consumes inventory data but does not own canonical inventory records. Shared services provide technical capabilities only.

## Current status

Skeleton only. Do not add implementation until a concrete catalogue capability is required and its source truth is established.

## Naming

Keep the module name lowercase and hyphenated: `efps-meta-catalogue-mgmnt`.

## Safety

Do not invent catalogue or property facts, silently change business rules, or commit credentials.