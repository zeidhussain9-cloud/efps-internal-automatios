# Slack Migration Handoff

## Completed in this branch

The shared Slack folder now contains:

- canonical capability README
- command surface
- channel topology
- bulk photo/re-verification runbook
- property verification runbook
- batch operations runbook
- Slack operations guide
- cleaned app manifest specification
- reusable Web API client
- inbound signature verification
- Slack-safe text/thread-control helpers
- routing constants
- tests for the reusable security/safety layer
- legacy-to-new implementation map

## Explicit obsolete material removed from the new design

Society approval is not used. No society approval command, queue, card, learning table, or Slack workflow is part of this repository's target architecture.

The old manifest's obsolete society references are not copied into the target manifest.

## Current temporary photo design

Webhook photo extraction is not currently available. Slack thread attachments are therefore the current operator-assisted photo collection mechanism. The canonical persistence target is the existing inventory row's `cloudinary_image_urls` field.

## Remaining integration activation work

This branch establishes the reusable capability and the complete operational specification. Production activation still requires wiring the owning modules' event/command handlers to this shared package, configuring approved runtime secrets, configuring actual new-repository Slack endpoints, installing/reinstalling the Slack app as required, and performing live API/event tests.

Do not claim those runtime steps are complete until verified.
