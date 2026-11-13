import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import { createClient } from 'npm:@supabase/supabase-js@2.117.2'

const EXPECTED_INTERNAL_KEY_SHA256 = 'a64a3cb25769eff7c88456645d5196cf5e4fa33fc1c9b80ac309f4a2d605c4c9'
const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
if (!supabaseUrl || !serviceRoleKey) throw new Error('Supabase server credentials are unavailable')
const supabase = createClient(supabaseUrl, serviceRoleKey, { auth: { persistSession: false, autoRefreshToken: false } })

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  return Array.from(new Uint8Array(digest)).map((x) => x.toString(16).padStart(2, '0')).join('')
}
function safeEqual(a: string, b: string): boolean {
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b)
  let diff = x.length ^ y.length
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0)
  return diff === 0
}
const uuid = (value: unknown) => typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)

Deno.serve(async (req) => {
  if (req.method !== 'POST') return Response.json({ error: 'POST required' }, { status: 405 })
  const internalKey = req.headers.get('x-efps-intake-auth') ?? ''
  if (!internalKey || !safeEqual(await sha256(internalKey), EXPECTED_INTERNAL_KEY_SHA256)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  let body: Record<string, unknown>
  try { body = await req.json() } catch { return Response.json({ error: 'Invalid JSON' }, { status: 400 }) }
  const pageId = String(body.page_id ?? '')
  if (!uuid(pageId)) return Response.json({ error: 'Invalid Notion page ID' }, { status: 400 })
  const operation = String(body.operation ?? '')
  let result
  if (operation === 'claim') {
    const payloadHash = String(body.payload_hash ?? '')
    if (!/^[a-f0-9]{64}$/i.test(payloadHash)) return Response.json({ error: 'Invalid payload hash' }, { status: 400 })
    result = await supabase.rpc('crm_claim_notion_inventory_intake', { p_source_page_id: pageId, p_payload_hash: payloadHash })
  } else if (operation === 'set_listing_id') {
    const listingId = String(body.listing_id ?? '').trim()
    if (!listingId) return Response.json({ error: 'Listing ID is required' }, { status: 400 })
    result = await supabase.rpc('crm_set_notion_inventory_listing_id', { p_source_page_id: pageId, p_listing_id: listingId })
  } else if (operation === 'finish') {
    const state = String(body.state ?? '')
    if (!['processed', 'needs_review', 'failed'].includes(state)) return Response.json({ error: 'Invalid terminal state' }, { status: 400 })
    result = await supabase.rpc('crm_finish_notion_inventory_intake', {
      p_source_page_id: pageId,
      p_processing_status: state,
      p_listing_page_id: String(body.listing_page_id ?? ''),
      p_processing_notes: String(body.note ?? '').slice(0, 1800),
    })
  } else {
    return Response.json({ error: 'Unsupported operation' }, { status: 400 })
  }
  if (result.error) {
    console.error('Notion inventory state operation failed', { operation, code: result.error.code })
    return Response.json({ error: 'Inventory state operation failed' }, { status: 500 })
  }
  if (operation === 'claim') return Response.json(result.data)
  return Response.json({ ok: true })
})
