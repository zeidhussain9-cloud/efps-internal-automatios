# Slack + Inventory Phase-1 Release Gate

This document defines what must be true before the new repository is considered production-ready for Inventory Phase 1.

## Scope

Phase 1 ends at a reliable inventory workflow:

`WhatsApp intake → raw row → deterministic Stage 2 → Maps resolution → validation → optional advisory AI → canonical row ready → Slack operational control/review → manual photo collection path`

Downstream Housing/Meta publishing is outside this release gate.

## Required production capabilities

### 1. Slack transport

- Slack Web API client exists under `shared/slack/`.
- Request signature verification exists and fails closed.
- Message posting, thread replies, history/replies, file lookup, reactions, pins, channel info and user info are supported as reusable primitives.
- No credentials are committed to Git.

### 2. Slack command surface

The new Phase-1 operational surface is the one top-level `/efps` command with these implemented families:

- `help`
- `status`
- `run`
- `show <listing_id>`
- `fix <listing_id> <field> <value>`
- `verify start|submit|next|skip|exit`
- `photos start|done|next|skip|exit`
- `bug report|submit|cancel|show|fix`
- `bugs`
- `pause`
- `resume`

No society approval command or society approval workflow is part of Phase 1.

### 3. Batch control

Scheduled and manual batch execution must expose operational status through Slack without making Slack part of canonical data persistence.

The batch flow must:

1. read canonical inventory rows;
2. process eligible Raw rows through deterministic Stage 2;
3. resolve Maps when a Maps URL is supplied;
4. validate the canonical record;
5. stop for human review when deterministic validation or required Maps verification fails;
6. apply advisory AI only after the deterministic gate passes;
7. publish a batch report to the inventory Slack channel;
8. leave the canonical sheet row as the source of truth.

### 4. Property verification

The Slack verification queue is driven from rows whose status is `Needs Review`.

The operator must be able to:

1. start verification;
2. receive one property at a time in a thread;
3. answer only fields requiring human attention;
4. use `skip`, `next`, and `exit` controls;
5. `submit` the corrections;
6. re-run deterministic dependencies and validation;
7. write the corrected canonical values back to the same row;
8. move the row out of `Needs Review` only after successful validation.

Verification does not create or update a separate society-approval/profile table.

### 5. Photo collection — temporary Phase-1 path

The current inbound webhook does not provide a reliable persisted photo-to-property association. Therefore Phase 1 uses Slack as the human-assisted bulk photo collection path.

Required behavior:

1. `/efps photos start` queries the sheet for the next processed property with blank `cloudinary_image_urls` and excludes `Rented Out` rows.
2. Slack posts a property message in the inventory channel and records the message thread timestamp.
3. The operator attaches any number of photos as replies in that exact thread; multiple replies are allowed.
4. The operator sends the bare thread word `done`.
5. The Slack/event worker obtains the attached files, uploads them to Cloudinary, preserves existing URLs, and writes the resulting URL list back to the same `Housing_Listings` row.
6. The queue is recalculated from the sheet so completed properties disappear from the queue automatically.
7. `skip` changes only the current session cursor; skipped properties remain eligible in later sessions.
8. `exit` ends the session without changing the property row.
9. If no photos are attached, nothing is written and the operator is told to attach them and retry `done`.
10. Partial/retry behavior must preserve already stored Cloudinary URLs and append subsequent successful uploads.

Manual entry of Cloudinary URLs is not the normal recovery path.

### 6. Phase-1 data safety

Stage 1/2 may write only its owned columns. Stage-3-owned lifecycle/posting fields remain protected.

For the current 48-column contract the Stage-1/2 write boundary is:

- `A:D`
- `F:AO`
- `AU`

Protected from Stage 1/2:

- `E` (`listing_state`)
- `AP:AT` downstream fields
- `AV` (`inventory_locked`)

### 7. Go-live runtime configuration

Before production readiness is claimed, the following must be configured and tested in the target environment:

- Slack bot token/signing secret through the approved secret mechanism.
- Slack slash-command endpoint.
- Slack event endpoint.
- Slack interactivity endpoint if buttons are enabled in the Phase-1 runtime.
- Bot membership in every operational channel used by Phase 1.
- Google Sheets credentials.
- Google Maps credentials where Maps verification is required.
- Cloudinary credentials for the manual photo path.
- WhAPI webhook/inbound listener configuration.

Never record secret values in this repository.

### 8. Runtime acceptance tests

Production readiness requires live verification of at least:

- `/efps help`
- `/efps status`
- `/efps run`
- `/efps show <listing_id>`
- `/efps fix <listing_id> <field> <value>` with ownership rejection tested
- `Needs Review` verification thread from start through `submit`
- photo session from `photos start` through thread attachments and `done`
- Cloudinary upload and same-row URL persistence
- no-photo retry behavior
- batch completion Slack report
- batch error/bug reporting
- pause/resume behavior
- Slack signature rejection for an invalid request

A source-code review is not a substitute for these live checks.

## Deterministic extraction acceptance

The release is complete only when the deterministic Stage-2 pipeline can safely process the existing inventory rows requested for migration/testing, including rows 2–26, without silently overwriting protected downstream fields.

Every row must be evaluated against the canonical 48-field schema and its deterministic rules. Rows that cannot pass required validation or Maps verification must remain explicitly reviewable rather than being guessed into a valid-looking state.

## Status vocabulary

Use only these runtime claims:

- `IMPLEMENTED` — source code/documentation exists and local tests pass.
- `CONFIGURED` — deployment configuration is present.
- `LIVE` — a real runtime probe succeeded.
- `NOT VERIFIED` — source exists but runtime evidence is missing.
- `BLOCKED` — a concrete prerequisite prevents the next acceptance test.
