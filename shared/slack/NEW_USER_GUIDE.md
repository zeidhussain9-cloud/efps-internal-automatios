# EFPS Slack Guide

This is the practical guide for using Slack as the EFPS operations panel. It is not a generic employee onboarding document.

## 1. Where to work

### Inventory

`#eps-wapi-pannel`

Use for property status, batch runs, field corrections and photo collection.

### Property verification

`#epf-prop-aprovals`

Use for human verification of inventory rows. The name is historical; this is **not** a society approval workflow.

### Leads

`#efps-leads`

Use for lead cards, lead threads and the dashboard.

### Runtime bugs

`#eps-runtime-error-bugs-reporting`

Use for manual and automatic runtime defect tracking.

## 2. First checks

Run `/efps status` in the inventory channel.

Use `/efps help` to see the supported command surface.

If the bot does not respond, do not assume the inventory pipeline is broken. Check Slack authentication/channel membership and runtime health separately.

## 3. Process a batch now

Run:

`/efps run`

Then wait for the batch report. The report is a summary of pipeline activity; it is not the source of truth for individual row values.

## 4. Inspect a property

Run:

`/efps show <listing_id>`

Use the linked sheet row for authoritative field values.

## 5. Correct a property

Run:

`/efps fix <listing_id> <field> <value>`

The correction is expected to re-run deterministic dependencies and validation before writing the same row.

Do not use this command to bypass Maps-owned, system-owned, or downstream-owned fields.

## 6. Add photos in bulk — current method

Because the current webhook does not extract/persist photo binaries, use Slack as the temporary photo collection interface.

1. Open `#eps-wapi-pannel`.
2. Run `/efps photos start`.
3. Wait for the property message.
4. Reply in that exact property's thread.
5. Attach all photos for that property.
6. Type `done` as a bare thread reply.
7. Wait for the save worker to process the attachments.
8. Confirm the same listing row now contains Cloudinary URLs.
9. Continue to the next property.
10. Use `skip` for a property you cannot complete and `exit` to stop.

Do not attach photos to another property's thread. Do not create a duplicate listing to recover from a photo problem.

For detailed recovery, use `REVERIFY_PHOTOS.md`.

## 7. Verify properties after batch processing

When the batch reports review-required rows:

1. Open `#epf-prop-aprovals`.
2. Run `/efps verify start`.
3. Answer the property's questions in its thread.
4. Reply `submit` when complete.
5. Confirm the canonical row after submission.
6. Continue with `next`, `skip`, or `exit`.

## 8. Bugs

Run `/efps bug report` to start a guided manual report.

Use `/efps bugs` to inspect open/unannounced bug records.

Use `/efps bug fix <BUG-ID> <note>` after the fix is actually applied.

## 9. Leads

Lead operations use persistent cards and buttons rather than a command-heavy interface. Cards should be updated in place when possible; the thread holds the conversation context.

## 10. Critical rules

- Slack is an operational interface, not the canonical inventory database.
- Do not invent fields, commands, channel purposes, or workflows.
- Do not use obsolete society approval commands.
- Do not manually overwrite downstream-owned values.
- Do not treat a Slack success message as proof of Google Sheets/Cloudinary persistence.
- Keep property photo attachments in the correct property thread.
- Keep credentials out of Git.
