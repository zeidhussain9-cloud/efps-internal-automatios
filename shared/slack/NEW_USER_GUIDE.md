# EFPS Slack Guide

This is the operator guide for the EFPS Slack control surface used during Inventory Phase 1.

## 1. Where Slack fits

Slack is the operational control and human-intervention surface. `Housing_Listings` remains the canonical inventory record.

The normal flow is:

`WhatsApp → Stage 1 raw row → Stage 2 deterministic processing → validation/AI gate → Slack report or review → canonical row ready`

Slack does not replace deterministic extraction and does not become a second inventory database.

## 2. Channels

### `#eps-wapi-pannel`

Use for inventory operations:

- `/efps status`
- `/efps run`
- `/efps show <listing_id>`
- `/efps fix <listing_id> <field> <value>`
- `/efps photos start`
- batch completion/error reports

### `#epf-prop-aprovals`

Use for **property verification only**. A `Needs Review` property is shown in a thread and the operator answers the missing/uncertain fields there.

### `#eps-runtime-error-bugs-reporting`

Use for runtime bug reports and bug closure.

### `#efps-leads`

Lead cards/dashboard. This is retained as part of the shared Slack capability, but it is not required to complete Inventory Phase-1 extraction.

## 3. Main command

Slack registers only one top-level slash command:

```text
/efps
```

The EFPS application routes the subcommand.

### Inventory commands

```text
/efps help
/efps status
/efps run
/efps show <listing_id>
/efps fix <listing_id> <field> <value>
/efps pause
/efps resume
```

### Property verification

```text
/efps verify start
```

Inside the property thread use the bare words:

```text
submit
skip
next
exit
```

### Bulk photos

```text
/efps photos start
```

Inside the property thread use:

```text
done
skip
next
exit
```

### Bug handling

```text
/efps bug report
/efps bugs
/efps bug show <BUG-ID>
/efps bug fix <BUG-ID> <note>
```

## 4. Bulk photo procedure — current Phase-1 method

The WhatsApp webhook currently does not reliably provide a persisted photo-to-property association. Therefore the Phase-1 operator must associate photos through the Slack property thread.

1. In `#eps-wapi-pannel`, run `/efps photos start`.
2. EFPS selects the next processed inventory row with no Cloudinary URLs and posts a property message.
3. Attach **all photos for that property** as replies in that exact thread. Multiple replies are allowed.
4. When finished, send the bare word `done` in that thread.
5. EFPS fetches the thread files, uploads them to Cloudinary, preserves existing URLs, and writes the URL list to the same inventory row.
6. The queue is recalculated from the sheet.
7. Continue with `next`, or let the session advance according to the implemented session flow.
8. Use `skip` only when intentionally deferring a property.
9. Use `exit` to end the session without changing the row merely because the session was closed.

### Never do this

- Do not use time-window matching to guess which property a photo belongs to.
- Do not post another property's photos in the current property thread.
- Do not create another inventory row for a photo problem.
- Do not delete existing Cloudinary URLs during recovery.
- Do not treat photo contents as proof of property identity.

## 5. Property verification during batch processing

A batch can leave a property as `Needs Review` when deterministic validation or required location verification cannot safely complete.

1. Run `/efps verify start` in the property-verification channel.
2. EFPS presents one review property at a time.
3. Answer the requested fields in the thread.
4. Use `skip` to leave a field blank or pass the property according to the session control.
5. When the answers are complete, reply `submit`.
6. The inventory module applies the corrections to the same row.
7. Deterministic dependencies are re-run.
8. Validation runs again.
9. Only a successfully validated correction is written as ready for the next step.

The verification flow does **not** create a society approval queue or society profile workflow.

## 6. What a batch report means

A batch report is an operational summary. Use `/efps status` to inspect current queue/state and `/efps run` to trigger an on-demand run when the schedules are active.

A Slack report must never be treated as the canonical data source. When a report and the sheet disagree, inspect the canonical row and pipeline state.

## 7. Manual correction

Use:

```text
/efps fix <listing_id> <field> <value>
```

The command must respect ownership boundaries. Maps-owned, system-owned, and downstream-owned fields are not arbitrary manual-edit fields.

A correction must be re-normalized and validated before the same row is persisted.

## 8. Session-thread rule

Slack slash commands start workflows. Session controls are plain thread words because a slash command is not the mechanism used for the thread interaction.

For photo sessions:

`done / skip / next / exit`

For verification sessions:

`submit / skip / next / exit`

## 9. What is intentionally not part of current Slack behavior

There is **no society approval workflow** in the new repository.

Do not add or revive:

- `/efps societies`
- `/efps society`
- society approval queue
- society approval card
- society approval state

These were contradictory legacy material and are explicitly obsolete.

## 10. Operational safety

- Never place tokens or signing secrets in Slack messages or Git.
- Treat Slack as an operational interface, not the source of truth.
- When runtime behavior is uncertain, use `NOT VERIFIED` rather than guessing.
- Preserve the canonical row and its ownership boundaries.
