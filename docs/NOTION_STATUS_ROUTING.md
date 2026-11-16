# Notion lifecycle routing, 16 November 2026

Approved scope: route current Notion intake, Housing edits and CRM mirror to the existing `Availability`, `Pipeline Status` and `live at` properties. Do not delete old properties, values or event history. No Slack revival, catalogue sending, bulk historical remap or expanded missing-photo validation.

- Raw Intake `Intake Status` remains New / Processing / Processed / Needs Review.
- A new Housing listing defaults Availability to Available. Successful processing produces Pipeline Status Ready To Post; a blocking review result produces Needs Review.
- Successful reruns preserve Posted or Removed. Availability, live at and downstream product/portal metadata are preserved. No channel is inferred from processing success. Required canonical state missing on an existing row stops that update rather than guessing from old statuses.
- Direct Housing edits are mirrored, not re-extracted. Availability feeds existing CRM `listing_state`; Pipeline Status feeds existing `business_status`; live at is retained as a list in source_record. Existing `intake_status` database data and prior source evidence are retained, not used to calculate the new lifecycle.
- Matching remains Available-only plus not deleted and the established customer filters. No new readiness gate is added.
- The unchanged deterministic 48-field extractor uses status/intake_status/listing_state internally as a scratch contract. The Notion lifecycle adapter does not read the four old Housing lifecycle properties and does not write them. These internal parser fields are not canonical business state or Notion output.
- Current publication/removal automation is not introduced. Existing channels and catalogue IDs do not prove a product is currently present.

Implementation: notion_lifecycle.py, notion_intake.py, notion-inventory-state Edge projection, inventory UI stage label and source-audit readers. Old Housing properties remain untouched. Rollout evidence and limits must be recorded separately; source changes alone do not establish deployment success.
