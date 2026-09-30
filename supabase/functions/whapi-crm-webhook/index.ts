import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import { createClient } from 'npm:@supabase/supabase-js@2'

const SOURCE_NUMBER = '+919148338801'
const SECRET_NAME = 'crm_whapi_webhook_token'
const MAX_MESSAGES = 100

const secretKeys = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') ?? '{}')
const adminKey = secretKeys.default ?? Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
if (!adminKey) throw new Error('Supabase secret key is unavailable')
const supabaseAdmin = createClient(Deno.env.get('SUPABASE_URL')!, adminKey)

function normalisePhone(value: unknown): string {
  const digits = String(value ?? '').split('@')[0].replace(/\D/g, '')
  if (digits.length === 10) return '+91' + digits
  if (digits.length === 11 && digits.startsWith('0')) return '+91' + digits.slice(1)
  if (digits.length === 12 && digits.startsWith('91')) return '+' + digits
  return ''
}

function safeEqual(a: string, b: string): boolean {
  const aa = new TextEncoder().encode(a)
  const bb = new TextEncoder().encode(b)
  let diff = aa.length ^ bb.length
  const n = Math.max(aa.length, bb.length)
  for (let i = 0; i < n; i += 1) diff |= (aa[i % Math.max(aa.length, 1)] ?? 0) ^ (bb[i % Math.max(bb.length, 1)] ?? 0)
  return diff === 0
}

function messageAt(value: unknown): string {
  if (typeof value === 'number' || /^\d+$/.test(String(value ?? ''))) {
    const n = Number(value)
    const ms = n < 10_000_000_000 ? n * 1000 : n
    const d = new Date(ms)
    if (Number.isFinite(d.valueOf())) return d.toISOString()
  }
  const d = new Date(String(value ?? ''))
  if (Number.isFinite(d.valueOf())) return d.toISOString()
  return new Date().toISOString()
}

function textBody(message: Record<string, unknown>): string | null {
  const text = message.text
  if (text && typeof text === 'object') {
    const body = String((text as Record<string, unknown>).body ?? '').trim()
    if (body) return body.slice(0, 4000)
  }
  for (const key of ['image', 'video', 'document', 'audio']) {
    const media = message[key]
    if (media && typeof media === 'object') {
      const caption = String((media as Record<string, unknown>).caption ?? '').trim()
      if (caption) return caption.slice(0, 4000)
    }
  }
  const button = message.button_reply
  if (button && typeof button === 'object') return String((button as Record<string, unknown>).title ?? (button as Record<string, unknown>).id ?? '').slice(0, 4000) || null
  return null
}

function media(message: Record<string, unknown>): { urls: string[]; filenames: string[] } {
  const urls: string[] = []
  const filenames: string[] = []
  for (const key of ['image', 'video', 'document', 'audio']) {
    const value = message[key]
    if (!value || typeof value !== 'object') continue
    const item = value as Record<string, unknown>
    const url = String(item.link ?? item.url ?? '').trim()
    const filename = String(item.filename ?? item.file_name ?? '').trim()
    if (url) urls.push(url)
    if (filename) filenames.push(filename)
  }
  return { urls, filenames }
}

async function expectedToken(): Promise<string> {
  const { data, error } = await supabaseAdmin.rpc('crm_get_webhook_secret')
  if (error) throw new Error('Webhook authentication configuration unavailable')
  return String(data ?? '')
}

Deno.serve(async (req) => {
  if (req.method !== 'POST') return Response.json({ error: 'POST required' }, { status: 405 })

  const expected = await expectedToken()
  const supplied = req.headers.get('x-crm-webhook-token') ?? ''
  if (!expected || !safeEqual(supplied, expected)) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  let payload: Record<string, unknown>
  try {
    payload = await req.json()
  } catch {
    return Response.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const rawMessages = Array.isArray(payload.messages) ? payload.messages : []
  const messages = rawMessages.slice(0, MAX_MESSAGES).filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object'))
  const results: Array<Record<string, unknown>> = []

  for (const message of messages) {
    const providerEventId = String(message.id ?? '').trim()
    if (!providerEventId) {
      results.push({ status: 'ignored', reason: 'message id missing' })
      continue
    }

    const fromMe = Boolean(message.from_me)
    const chat = String(message.chat_id ?? '')
    const contact = fromMe ? String(message.to ?? chat) : String(message.from ?? chat)
    const phone = normalisePhone(contact)
    const direction = fromMe ? 'Outgoing' : 'Incoming'
    const type = String(message.type ?? 'text').trim() || 'text'
    const body = textBody(message)
    const senderName = String((fromMe ? message.to_name : message.from_name) ?? message.contact_name ?? '').trim() || null
    const mediaValue = media(message)
    const sentAt = messageAt(message.timestamp ?? message.message_at)

    if (!phone) {
      results.push({ status: 'failed', provider_event_id: providerEventId, reason: 'customer phone could not be normalized' })
      continue
    }

    const { data: event, error: recordError } = await supabaseAdmin.rpc('crm_record_webhook_event', {
      p_provider: 'whapi',
      p_provider_event_id: providerEventId,
      p_source_number: SOURCE_NUMBER,
      p_phone: phone,
      p_direction: direction,
      p_message_type: type,
      p_payload: message,
      p_message_at: sentAt,
    })

    if (recordError || !Array.isArray(event) || !event[0]) {
      results.push({ status: 'failed', provider_event_id: providerEventId, reason: recordError?.message ?? 'event record failed' })
      continue
    }

    const row = event[0] as Record<string, unknown>
    const eventId = Number(row.event_id)
    if (row.processing_status === 'processed') {
      results.push({ status: 'duplicate', provider_event_id: providerEventId, lead_id: row.lead_id, message_id: row.message_id })
      continue
    }

    const { data: processed, error: processError } = await supabaseAdmin.rpc('crm_process_webhook_event', {
      p_event_id: eventId,
      p_source_number: SOURCE_NUMBER,
      p_phone: phone,
      p_direction: direction,
      p_message_type: type,
      p_body: body,
      p_sender_name: senderName,
      p_media_urls: mediaValue.urls.length ? mediaValue.urls : null,
      p_media_filenames: mediaValue.filenames.length ? mediaValue.filenames : null,
      p_message_at: sentAt,
    })

    if (processError) {
      await supabaseAdmin.rpc('crm_fail_webhook_event', { p_event_id: eventId, p_error: processError.message })
      results.push({ status: 'failed', provider_event_id: providerEventId, event_id: eventId, reason: processError.message })
      continue
    }

    results.push({ status: 'processed', provider_event_id: providerEventId, ...((processed ?? {}) as Record<string, unknown>) })
  }

  return Response.json({ ok: true, source_number: SOURCE_NUMBER, received: messages.length, results })
})
