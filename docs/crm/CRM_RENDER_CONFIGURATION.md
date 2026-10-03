# EFPS CRM — Render Configuration

> **Verified 2026-10-03 18:04 IST (12:34 UTC).**

## Production service

- Service: `srv-darsv560tbcc73cu4ip0`
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: `crm-ui-dashboard`
- Current release commit: `e375c1f811e962e140caba2c964fb05cd94ab02a`
- Auto-deploy: enabled on commit

## Runtime boundaries

The service exposes the CRM UI, protected read/write routes, the signed AI scheduler endpoint, and the signed inventory-sync endpoint. Database credentials and AI provider credentials remain server-side secrets.

Automatic WhatsApp sending is disabled. AI drafts must pass the deterministic pre-send grounding check and remain operator-controlled.

## Current scheduler configuration

- Webhook reconciliation: Supabase cron, every minute.
- Inventory reconciliation: Supabase cron, every five minutes.
- Unified AI scheduler: Supabase cron, every six hours.

## Credential hardening

The application uses the AWS SDK credential chain. Production least-privilege IAM rotation is an external provisioning task and is not represented as complete until a new authorized AWS identity is configured and the old identity is retired.