# EFPS CRM UI Dashboard — Current State

> **Verified 2026-10-03 18:04 IST (12:34 UTC).**

## Production identity

- Render service: `srv-darsv560tbcc73cu4ip0`
- Production URL: https://easyfind-crm-d01-d05.onrender.com
- Deployment branch: `crm-ui-dashboard`
- Current release commit: `e375c1f811e962e140caba2c964fb05cd94ab02a`
- Supabase project: `qttcutwzehtskfcwxkwj`
- Production WhatsApp source: `+919148338801`

## Operational status

The dashboard uses the production Supabase CRM data path. Webhook events are durably recorded before reconciliation. Inventory is a read-only CRM mirror of the canonical Housing_Listings source. AI analysis is persisted and operator-controlled; WhatsApp sending is manual.

## Current hardening

- Lead status and contact classification are separate persisted concepts.
- Overdue follow-up attention is based only on persisted open follow-ups.
- Inventory uses full-inventory KPI summaries, filtering, sorting and stale-response protection.
- Webhook reconciliation is automatic and idempotent.
- Scheduled AI uses per-lead evaluation checkpoints and persisted idempotency keys.
- OOC automation uses only the controlled geographic vocabulary; ambiguous/selective/unknown locations remain review-required.
- D08 current UI and operator-control handoff is documented in the CRM design and hardening documents.

## Current database snapshot

186 leads · 7,573 messages · 1,256 webhook events · 214 AI runs · 214 drafts · 88 active inventory listings.

## Release note

This document is a point-in-time production statement. Do not copy its values into future documentation without re-verifying the live database and Render deployment.