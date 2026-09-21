# Slack Boundary for Inventory Phase 1

This document fixes what Slack must and must not do for the Inventory Phase-1 release.

## Slack is an operational surface, not the inventory source of truth

The canonical inventory record remains `Housing_Listings`. Slack can initiate an operation, collect human input, and report results, but it must not become a second inventory database.

## Phase-1 workflows

### A. Batch processing

Slack can start a batch with `/efps run`, show status, and publish the completion report. The deterministic pipeline owns the processing decision and the sheet owns the resulting canonical row.

### B. Property verification — REMOVED

The automated Slack verification queue (previously workflow B) has been removed. Properties requiring corrections should be handled through direct Sheet editing or future admin tools. The `_save_verification()` function and `PROPERTY_VERIFICATION_CHANNEL` listener have been removed from `events_handler.py`.

### C. Bulk photo collection

Because the current WhatsApp webhook path does not reliably extract/persist photo binaries with a property association, Phase 1 uses Slack threads as the association mechanism.

The exact operational path is:

`/efps photos start`
→ select next processed row with blank `cloudinary_image_urls`
→ post property card
→ record Slack thread timestamp
→ operator attaches photos as thread replies
→ bare `done`
→ fetch thread files
→ upload to Cloudinary
→ append/preserve URLs
→ write same inventory row
→ recompute queue

No time-window matching, sender guessing, or property inference is permitted.

## Required channel roles

- `#eps-wapi-pannel`: inventory operations, batch reports, photo sessions, catalogue sessions, property entry.
- `#eps-runtime-error-bugs-reporting`: runtime and bug handling.
- `#efps-leads`: lead operations are retained in Slack capability documentation but are outside the inventory-only Phase-1 acceptance path unless the owning lead module is separately activated.

`#epf-prop-aprovals` is no longer a required channel. The `/efps verify` workflow that used it has been removed.

The exact channel identifiers are maintained in `CHANNELS.md` and must not be invented in code.

## Explicit exclusion

Society approval is **not** a Phase-1 workflow. Do not add, resurrect, document as current, or route any society-approval command, queue, card, or approval state.

## Production readiness meaning

Inventory Phase 1 is ready only when the source repository contains the necessary implementation and the deployed environment passes the release-gate runtime checks. A repository containing Slack client code alone is not sufficient to claim live production integration.
