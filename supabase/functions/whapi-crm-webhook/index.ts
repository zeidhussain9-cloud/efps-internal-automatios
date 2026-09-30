import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import { createClient } from 'npm:@supabase/supabase-js@2'

const SOURCE_NUMBER = '+919148338801'
const secretKeys = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') ?? '{}')
const adminKey = secretKeys.default ?? Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
if (!adminKey) throw new Error('Supabase secret key is unavailable')
const supabaseAdmin = createClient(Deno.env.get('SUPABASE_URL')!, adminKey)

function normalisePhone(value: unknown): string | null {
  const digits = String(value ?? '').split('@')[0].replace(/\D/g, '')
  if (digits.length === 10) return '+91' + digits
  if (digits.length === 11 && digits.startsWith('0')) return '+91' + digits.slice(1)
  if (digits.length === 12 && digits.startsWith('91')) return '+' + digits
  return null
}

function safeEqual(a: string, b: string): boolean {
  const aa = new TextEncoder().encode(a)
  const bb = new TextEncoder().encode(b)
  let diff = aa.length ^ bb.length
  const n = Math.max(aa.length, bb.length)
  for (let i = 0; i < n; i++) diff |= (aa[i % Math.max(aa.length, 1)] ?? 0) ^ (bb[i % Math.max(bb.length, 1)] ?? 0)
  return diff === 0
}

async function sha256(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(digest)).map(v => v.toString(16).padStart(2, '0')).join('')
}

function messageAt(value: unknown): string {
  const n = Number(value)
  if (Number.isFinite(n) && n > 0) {
    const ms = n < 10_000_000_000 ? n * 1000 : n
    const d = new Date(ms)
    if (Number.isFinite(d.valueOf())) return d.toISOString()
  }
  const d = new Date(String(value ?? ''))
  return Number.isFinite(d.valueOf()) ? d.toISOString() : new Date().toISOString()
}

function eventType(payload: Record<string, unknown>): string {
  const event = payload.event
  if (event && typeof event === 'object') {
    const e = event as Record<string, unknown>
    const type = String(e.type ?? '').trim()
    const action = String(e.event ?? '').trim()
    if (type || action) return [type, action].filter(Boolean).join('.')
  }
  return 'unknown'
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
  if (button && typeof button === 'object') {
    return String((button as Record<string, unknown>).title ?? (button as Record<string, unknown>).id ?? '').slice(0, 4000) || null
  }
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

function messagePhone(message: Record<string, unknown>): string | null {
  const fromMe = Boolean(message.from_me)
  return normalisePhone(fromMe ? (message.to ?? message.chat_id) : (message.from ?? message.chat_id))
}

async function recordEvent(args: {
  payload: Record<string, unknown>
  item: Record<string, unknown> | null
  index: number
}) {
  const { payload, item, index } = args
  const type = eventType(payload)
  const message = item
  const providerEventId = message ? String(message.id ?? '').trim() || null : null
  const phone = message ? messagePhone(message) : null
  const fromMe = message ? Boolean(message.from_me) : false
  const direction = message ? (fromMe ? 'Outgoing' : 'Incoming') : null
  const messageType = message ? String(message.type ?? 'text').trim() || 'text' : 'event'
  const body = message ? textBody(message) : null
  const senderName = message ? String((fromMe ? message.to_name : message.from_name) ?? message.contact_name ?? '').trim() || null : null
  const mediaValue = message ? media(message) : { urls: [], filenames: [] }
  const sentAt = messageAt(message?.timestamp ?? message?.message_at ?? (payload as Record<string, unknown>).timestamp)
  const fingerprint = await sha256(JSON.stringify({ payload, index, providerEventId }))

  const { data: eventRows, error: recordError } = await supabaseAdmin.rpc('crm_record_whapi_event', {
    p_provider: 'whapi',
    p_event_type: type,
    p_provider_event_id: providerEventId,
    p_source_number: SOURCE_NUMBER,
    p_phone: phone,
    p_direction: direction,
    p_message_type: messageType,
    p_payload: message ?? payload,
    p_message_at: sentAt,
    p_fingerprint: fingerprint,
  })
  if (recordError || !Array.isArray(eventRows) || !eventRows[0]) {
    return { status: 'failed', provider_event_id: providerEventId, reason: recordError?.message ?? 'event record failed' }
  }

  const row = eventRows[0] as Record<string, unknown>
  const eventId = Number(row.event_id)
  if (!phone || !direction) return { status: 'received', event_id: eventId, event_type: type }

  const { data: processed, error: processError } = await supabaseAdmin.rpc('crm_process_whapi_message', {
    p_event_id: eventId,
    p_source_number: SOURCE_NUMBER,
    p_phone: phone,
    p_direction: direction,
    p_message_type: messageType,
    p_body: body,
    p_sender_name: senderName,
    p_media_urls: mediaValue.urls.length ? mediaValue.urls : null,
    p_media_filenames: mediaValue.filenames.length ? mediaValue.filenames : null,
    p_message_at: sentAt,
  })
  if (processError) {
    await supabaseAdmin.rpc('crm_fail_webhook_event', { p_event_id: eventId, p_error: processError.message })
    return { status: 'failed', event_id: eventId, provider_event_id: providerEventId, reason: processError.message }
  }
  return { status: 'processed', event_id: eventId, provider_event_id: providerEventId, ...((processed ?? {}) as Record<string, unknown>) }
}

Deno.serve(async (req) => {
  if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method)) return Response.json({ error: 'Webhook method not supported' }, { status: 405 })

  const expected = Deno.env.get('CRM_WHAPI_WEBHOOK_TOKEN') ?? ''
  const supplied = req.headers.get('x-crm-webhook-token') ?? ''
  if (!expected || !safeEqual(supplied, expected)) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  let payload: Record<string, unknown>
  try {
    payload = await req.json()
  } catch {
    return Response.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const results: Array<Record<string, unknown>> = []
  const messages = Array.isArray(payload.messages) ? payload.messages : []
  if (messages.length) {
    for (let i = 0; i < Math.min(messages.length, 100); i++) {
      const item = messages[i]
      if (item && typeof item === 'object') results.push(await recordEvent({ payload, item: item as Record<string, unknown>, index: i }))
    }
  } else {
    results.push(await recordEvent({ payload, item: null, index: 0 }))
  }

  return Response.json({
    ok: true,
    source_number: SOURCE_NUMBER,
    event_type: eventType(payload),
    received_events: results.length,
    results,
  })
})