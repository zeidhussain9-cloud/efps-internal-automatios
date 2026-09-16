# Live-System Migration Map — 2026-09-16

This document records the approved migration boundary for the live-system migration from `efps-platform` into `efps-internal-automatios`.

## A. CURRENT MAIN — ALREADY PRESENT / RETAINED

The latest canonical `main` already contains the Lead Management business implementation, Slack command/interactive/events endpoints, WhAPI webhook normalization, shared Sheets/Maps/Cloudinary/Credentials/Slack/WhAPI capabilities, and the canonical Inventory Phase-1/Stage-2 implementation. These current implementations are retained rather than replaced by older migration-branch versions.

## B. MIGRATE / RECONCILE

| Live capability | Source | Destination | Responsibility | State |
|---|---|---|---|---|
| Inventory Stage-1 live intake | approved migration boundary | `modules/efps-inventory-mgmnt/src/inventory_runtime.py` | durable session capture, deduplication, raw intake, listing identity, handoff to canonical pipeline | reconciled |
| Scheduled Raw-row worker | migration `handler.py` | root `handler.py` | dispatch only Raw rows to canonical Inventory pipeline | reconciled |
| Live WhAPI routing fix | migration runtime intent + current `main` webhook | root `webhook_handler.py` | route inventory listeners to Stage 1; other inbound traffic to Lead | reconciled |
| Stage-1 session runtime resource | migration infrastructure requirement | `template.yaml` `SessionsTableArn` | provide `efps-sessions` access to webhook runtime | reconciled |
| Lead Management | approved legacy behavior + current main implementation | `modules/efpd-lead-mgmnt/` | Lead state, persistence, cards, audit, dashboard, stream/digest operations | retained on latest main |
| Slack live endpoints | approved migration capability + current main implementation | root Slack handlers/shared Slack | commands, interactive actions, Events API | retained on latest main |

## C. INVENTORY RESPONSIBILITY BOUNDARY

The new repository's existing Inventory implementation is authoritative.

The migration includes **only** the live Stage-1 integration boundary. The Stage-1 adapter delegates completed sessions to the existing canonical `pipeline.process_closed_session()` implementation.

The following legacy responsibilities are explicitly excluded and must not be copied, adapted, reconciled, or reproduced:

- extraction
- source segmentation
- normalization
- deterministic business rules
- field resolution
- property processing
- validation/business logic
- Stage-2 pipeline
- legacy Inventory tests or historical processing hacks

Inventory-adjacent code is accepted only when its responsibility is integration/runtime boundary work. Operator workflows that implement Inventory business processing remain outside this migration unless separately approved.

## D. OUT OF SCOPE

- legacy Inventory processing implementation
- legacy Inventory parsing/extraction/business rules
- Meta Catalogue publishing
- Housing.com publishing
- website/downstream publishing
- downstream lifecycle automation
- Society Approvals

## E. RUNTIME ACCEPTANCE — NOT CLAIMED BY THIS COMMIT

- production AWS deployment and final identity
- final endpoint URLs
- Lambda secret injection
- Slack app installation, bot membership, command/event registration and live permissions
- WhAPI destination registration/token relationship
- Cloudflare/User-Agent compatibility of the deployed canonical transport
- synthetic Inventory traffic through the final destination
- old-runtime zero required traffic
- final cutover

## Source authority

1. User-approved migration rules
2. Current new-repository canonical implementations/architecture
3. Verified current live behavior/configuration
4. Legacy implementation for approved migration components
5. Repository documentation
6. Runtime verification

No unverified legacy assumption may redefine the new Inventory implementation.
