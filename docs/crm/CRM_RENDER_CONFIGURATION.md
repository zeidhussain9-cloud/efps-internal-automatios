# EFPS CRM — Render Configuration

> Verified 2026-10-03 20:26 IST. Older candidate/deployment statements below are historical and superseded.

## Production service

- Service: srv-darsv560tbcc73cu4ip0
- URL: https://easyfind-crm-d01-d05.onrender.com
- Branch: crm-ui-dashboard
- Auto-deploy: enabled on commit

## Runtime boundaries

- Webhook ingress is Supabase-first and durable; Render is not the WhatsApp webhook persistence boundary.
- Pending WhatsApp group messages are routed to group_message / Group Message / Unqualified before CRM lead promotion can occur.
- Inventory sync endpoint is signed and invoked by Supabase cron.
- AI scheduler endpoint is HMAC-protected and invoked by Supabase cron.
- Automatic WhatsApp sending remains disabled; drafts require operator review and pre-send grounding.

## Release verification

A candidate is not production-live until Render reports the candidate SHA live and the production health/process audit is rerun. This document must not contain an older SHA as the current live commit.

## External credential hardening

AWS least-privilege rotation requires authorized AWS IAM administration. Do not mark the rotation complete based only on repository configuration.