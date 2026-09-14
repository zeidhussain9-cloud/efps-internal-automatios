# Slack Migration Handoff

## Completed in this branch

The shared Slack folder contains the reusable Phase-1 capability and its operational specification:

- canonical capability README
- command surface
- channel topology
- exact Phase-1 bulk-photo operator flow
- photo re-verification/recovery runbook
- property verification runbook
- batch operations runbook
- EFPS Slack operator guide
- cleaned app manifest specification
- reusable Web API client
- inbound signature verification
- Slack-safe text/thread-control helpers
- routing constants
- tests for the reusable security/safety layer
- legacy-to-new implementation map
- Inventory Phase-1 release gate
- Phase-1 Slack boundary

## Explicit obsolete material removed from the new design

Society approval is not used. No society approval command, queue, card, learning table, or Slack workflow is part of this repository's target architecture.

The old manifest's obsolete society references are not copied into the target manifest.

## Current temporary photo design

Webhook photo extraction is not currently available. Slack thread attachments are therefore the current operator-assisted photo collection mechanism. The canonical persistence target is the existing inventory row's `cloudinary_image_urls` field.

The operator must start from `/efps photos start`, attach all images for one property in the exact property thread, and reply `done` as a bare word. The worker must upload to Cloudinary, preserve existing URLs, write the same row, and recompute the queue.

## Inventory Phase-1 target

The new repository also contains a deterministic-first batch runner for existing canonical rows with `intake_status = Raw` and non-empty `raw_message_text`. It is designed to reuse the same Stage-2 processing path as completed webhook sessions and preserve Stage-3-owned columns.

Rows that cannot be safely completed remain explicitly reviewable; no missing fact is guessed into the sheet.

## Remaining integration activation work

This branch establishes the source implementation and operational specification, but production activation still requires:

- wiring the owning Slack command/event handlers to `shared/slack`;
- configuring approved runtime Slack secrets;
- configuring the actual new-repository slash/event/interactivity endpoints;
- installing/reinstalling the Slack app as required;
- ensuring bot membership in required channels;
- configuring live Google Sheets, Maps and Cloudinary dependencies;
- performing live API/event/photo/file/thread acceptance tests.

Do not claim `LIVE` until those runtime checks succeed.
