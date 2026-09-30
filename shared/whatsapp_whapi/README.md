# Shared WhAPI transport

This package contains only technical WhatsApp/WhAPI transport primitives: authentication, channel/settings access, webhook payload normalization and provider-safe message parsing.

## CRM live path

The CRM does not use source listeners, inventory listeners, lead listeners, polling, or a server-side WhAPI fetch loop. The production CRM path is:

`WhAPI messages webhook -> Supabase Edge Function -> crm_webhook_events -> crm_leads + crm_messages -> Supabase Realtime -> CRM UI`

The connected CRM source is `+919148338801`. Every accepted webhook message is treated as lead activity. Existing leads receive another chronological message; a previously unseen customer phone creates a lead row directly.

The CRM does not send WhatsApp messages automatically.

## Parser boundary

The shared parser normalizes common text, link-preview, location, image, video, document and audio message shapes. It does not decide whether a message is inventory, a lead, a promotion or any other business object.

Webhook event names and live settings must be verified against the provider's current settings before a live configuration change. This module does not mutate live provider settings automatically.
