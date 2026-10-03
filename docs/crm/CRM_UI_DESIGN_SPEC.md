# EFPS CRM — UI Design & Operational Handoff

> **Current verified snapshot: 2026-10-03 18:04 IST (12:34 UTC). This document is the D08 handoff baseline.**

## Product structure

The CRM presents Dashboard, Leads Inbox, Contact Classification, Inventory, AI & Drafts, and Audit views against a single protected production data path.

## Lead presentation

Lead cards expose operational Lead Status separately from Contact Classification. Status colors remain secondary to the text label. Customer identity uses persisted display name/phone data; no classification or risk state is inferred from age, budget or message volume.

## Inventory presentation

Inventory uses server-side search/filter/sort/pagination. KPI cards represent the full inventory dataset rather than the current page. Images are read from persisted Cloudinary URLs. Reserved source fields outside A:AT are not exposed as CRM-owned write fields.

## AI workspace

AI uses the full persisted lead workspace for manual analysis and checkpointed scheduled analysis. Runs, drafts, provider/model provenance and evidence are persisted. Drafts are stale-checked and must pass deterministic pre-send grounding before WhatsApp is opened. Sending remains manual.

## OOC policy

`Out of Coverage Area` is a Layer-2 lead status. Automatic assignment is permitted only when every requested preferred location exactly matches the controlled out-of-coverage vocabulary. Selective service areas, mixed in/out selections and unknown free-text locations remain review-required.

## D08 acceptance

The handoff is complete for the current production UI contract because navigation, lead-status presentation, classification separation, inventory interaction, AI operator controls, audit visibility, privacy controls and mobile regression requirements are documented against the current implementation.

Future visual changes must update this handoff and the current-state document together.