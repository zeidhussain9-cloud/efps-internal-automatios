# Live-System Migration Map — 2026-09-16

This document records the approved migration boundary for the live-system migration from `efps-platform` into `efps-internal-automatios`.

## A. MIGRATE

| Live capability | Verified source | New destination | Owner | Validation |
|---|---|---|---|---|
| Lead stages/actions/state | `modules/efps-whapi-panel/src/leads.py` | `modules/efpd-lead-mgmnt/src/leads.py` | Lead module | unit tests + DynamoDB integration |
| Lead persistence/interactions/audit | `src/db.py`, `src/audit.py` | lead module `db.py` / `audit.py` | Lead module | schema + mocked DB tests |
| Lead Slack cards/dashboard | `src/lead_card.py`, `src/digest.py` | lead module; shared Slack transport | Lead module | mocked Slack tests |
| Lead stream/digest worker | `leads_worker.py` | root `leads_worker.py` + lead module | Lead module | SAM/template inspection + runtime test |
| Slack slash command endpoint | `commands_handler.py` + `src/commands.py` | root `commands_handler.py`, root `commands.py` | shared Slack + root adapter | signature/routing test |
| Slack interactive endpoint | `interactive_handler.py` | root `interactive_handler.py` | shared Slack + lead module | signature/modal test |
| Slack Events endpoint | `events_handler.py` | root `events_handler.py` | shared Slack + inventory/lead owners | signature/thread test |
| Runtime bug surface | legacy `src/bugs.py`, `src/crash_report.py` | `shared/slack/bugs.py`, `shared/slack/crash_report.py` | shared Slack | mocked state/error tests |
| Live WhAPI listener routing | legacy webhook configuration | `webhook_handler.py` + `shared/whatsapp_whapi/` | webhook/shared provider | synthetic non-inventory probe |
| Inventory Stage-1 live intake connection | legacy webhook boundary only | `modules/efps-inventory-mgmnt/src/inventory_runtime.py` | Inventory module | synthetic Inventory message; no legacy processing |
| Required AWS runtime resources | legacy SAM as reference | root `template.yaml` | infrastructure | SAM validation + deployment verification |

## B. ALREADY PRESENT — DO NOT DUPLICATE

- `shared/google_sheets/`
- `shared/google_maps/`
- `shared/cloudinary/`
- `shared/credentials/`
- `shared/whatsapp_whapi/`
- `shared/slack/`
- canonical 48-column `Housing_Listings` schema
- new deterministic Inventory Stage-2 implementation

## C. NEW REPOSITORY AUTHORITATIVE — DO NOT TAKE FROM LEGACY

All Inventory extraction, source segmentation, field resolution, normalization, validation, Maps resolution, deterministic processing, provenance, and Stage-2 behavior remain exclusively the new repository implementation.

## D. OUT OF SCOPE

- legacy Inventory processing implementation
- legacy Inventory parsing/extraction/business rules
- Meta Catalogue publishing
- Housing.com publishing
- website/downstream publishing
- downstream lifecycle automation
- Society Approvals

## E. NEEDS LIVE VERIFICATION

- current live WhAPI webhook URL and token relationship
- Cloudflare/User-Agent compatibility of the canonical WhAPI transport
- final Slack app installation, bot membership, command/event endpoint registration, and live permissions
- production AWS deployment identity and final endpoint URLs
- production secret injection mechanism for Lambda runtime
- final cutover/zero-traffic confirmation for the old runtime

## Source authority

1. User-approved migration rules
2. Current new-repository canonical implementations/architecture
3. Verified current live behavior/configuration
4. Legacy implementation for approved migration components
5. Repository documentation
6. Runtime verification

No unverified legacy assumption may redefine the new Inventory implementation.
