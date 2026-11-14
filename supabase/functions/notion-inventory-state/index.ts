import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import { createClient } from 'npm:@supabase/supabase-js@2.117.2'
import { missingActivePageRows, responseForOperation } from './response-contract.mjs'

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
  const operation = String(body.operation ?? '')
  const pageScopedOperations = new Set(['claim', 'set_listing_id', 'finish', 'allocate_listing_id', 'delete_inventory', 'find_inventory', 'sync_inventory'])
  if (pageScopedOperations.has(operation) && !uuid(pageId)) return Response.json({ error: 'Invalid Notion page ID' }, { status: 400 })
  let result
  if (operation === 'record_webhook_event') {
    const eventKey = String(body.event_key ?? '')
    const payloadSha256 = String(body.payload_sha256 ?? '')
    const eventPayload = body.payload
    if (!eventKey || eventKey.length > 200 || !/^[a-f0-9]{64}$/i.test(payloadSha256) ||
      !eventPayload || typeof eventPayload !== 'object' || Array.isArray(eventPayload)) {
      return Response.json({ error: 'Invalid Notion webhook event' }, { status: 400 })
    }
    const optionalUuid = (value: unknown) => value === null || value === undefined || value === '' || uuid(value)
    if (!optionalUuid(body.notion_event_id) || !optionalUuid(body.workspace_id) ||
      !optionalUuid(body.subscription_id) || !optionalUuid(body.integration_id) ||
      !optionalUuid(body.entity_id) || !optionalUuid(body.page_id)) {
      return Response.json({ error: 'Invalid Notion event identifier' }, { status: 400 })
    }
    const attempt = body.attempt_number == null ? null : Number(body.attempt_number)
    if (attempt !== null && (!Number.isInteger(attempt) || attempt < 1 || attempt > 8)) {
      return Response.json({ error: 'Invalid Notion delivery attempt' }, { status: 400 })
    }
    result = await supabase.rpc('crm_record_notion_webhook_event', {
      p_event_key: eventKey,
      p_notion_event_id: body.notion_event_id || null,
      p_event_type: String(body.event_type ?? 'unknown').slice(0, 200),
      p_page_id: body.page_id || null,
      p_event_timestamp: body.event_timestamp || null,
      p_attempt_number: attempt,
      p_payload: eventPayload,
      p_payload_sha256: payloadSha256.toLowerCase(),
    })
  } else if (operation === 'update_webhook_event') {
    const eventSourceKey = String(body.event_row_id ?? '')
    const status = String(body.status ?? '')
    if (!eventSourceKey.startsWith('notion-webhook:') || eventSourceKey.length > 240 || !['accepted', 'queued', 'processing', 'processed', 'needs_review', 'failed', 'rejected', 'unsupported', 'ignored'].includes(status)) {
      return Response.json({ error: 'Invalid Notion webhook event transition' }, { status: 400 })
    }
    const optionalUuid = (value: unknown) => value === null || value === undefined || value === '' || uuid(value)
    if (!optionalUuid(body.page_id) || !optionalUuid(body.listing_page_id)) {
      return Response.json({ error: 'Invalid Notion webhook page reference' }, { status: 400 })
    }
    const outcome = body.outcome
    if (outcome !== null && outcome !== undefined && (typeof outcome !== 'object' || Array.isArray(outcome))) {
      return Response.json({ error: 'Invalid Notion webhook outcome' }, { status: 400 })
    }
    result = await supabase.rpc('crm_update_notion_webhook_event', {
      p_event_source_key: eventSourceKey,
      p_processing_status: status,
      p_aws_request_id: String(body.aws_request_id ?? '').slice(0, 200) || null,
      p_processing_error: String(body.error ?? '').slice(0, 1800) || null,
      p_processing_outcome: outcome ?? null,
      p_page_id: body.page_id || null,
      p_listing_id: String(body.listing_id ?? '').slice(0, 200) || null,
      p_listing_page_id: body.listing_page_id || null,
      p_validation_status: ['rejected', 'unsupported', 'ignored'].includes(status) ? status : null,
    })
  } else if (operation === 'claim') {
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
  } else if (operation === 'allocate_listing_id') {
    result = await supabase.rpc('crm_allocate_notion_inventory_listing_id', { p_source_page_id: pageId })
  } else if (operation === 'delete_inventory') {
    const existing = await supabase.from('crm_inventory_snapshot').select('listing_id')
      .eq('source_kind', 'housing_notion').eq('source_record->>notion_page_id', pageId).maybeSingle()
    if (existing.error) return Response.json({ error: 'Inventory lookup failed' }, { status: 500 })
    if (existing.data?.listing_id) {
      const deletedAt = new Date().toISOString()
      const updated = await supabase.from('crm_inventory_snapshot').update({ deleted_at: deletedAt, last_synced_at: deletedAt })
        .eq('listing_id', existing.data.listing_id)
      if (updated.error) return Response.json({ error: 'Inventory delete sync failed' }, { status: 500 })
    }
    return Response.json({ ok: true, found: Boolean(existing.data?.listing_id) })
  } else if (operation === 'find_inventory') {
    const existing = await supabase.from('crm_inventory_snapshot').select('listing_id,deleted_at,source_hash')
      .eq('source_kind', 'housing_notion').eq('source_record->>notion_page_id', pageId).maybeSingle()
    if (existing.error) return Response.json({ error: 'Inventory lookup failed' }, { status: 500 })
    return Response.json({ found: Boolean(existing.data?.listing_id), listing_id: existing.data?.listing_id ?? '', deleted_at: existing.data?.deleted_at ?? null, source_hash: existing.data?.source_hash ?? '' })
  } else if (operation === 'reconcile_pages') {
    const rawIds = body.active_page_ids
    if (!Array.isArray(rawIds) || rawIds.length < 1 || rawIds.length > 500 || rawIds.some((id) => !uuid(id))) {
      return Response.json({ error: 'A non-empty list of valid active Notion page IDs is required' }, { status: 400 })
    }
    const activeIds = rawIds.map((id) => String(id).toLowerCase())
    const rawListings = body.active_listings
    if (!Array.isArray(rawListings) || rawListings.length > 500 || rawListings.some((item) => {
      if (!item || typeof item !== 'object' || Array.isArray(item)) return true
      const mapping = item as Record<string, unknown>
      return !uuid(mapping.page_id) || !activeIds.includes(String(mapping.page_id).toLowerCase()) ||
        !/^EF-\d{4}-[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{4}$/.test(String(mapping.listing_id ?? ''))
    })) return Response.json({ error: 'Invalid active Notion Listing ID mappings' }, { status: 400 })
    const current = await supabase.from('crm_inventory_snapshot').select('listing_id,source_record')
      .eq('source_kind', 'housing_notion').is('deleted_at', null)
    if (current.error) return Response.json({ error: 'Inventory reconciliation lookup failed' }, { status: 500 })
    const mappings = rawListings as Array<{ page_id: string; listing_id: string }>
    let listingIdsReconciled = 0
    if (mappings.length) {
      const reconciled = await supabase.rpc('crm_reconcile_notion_inventory_event_listing_ids', {
        p_source_page_ids: mappings.map((item) => item.page_id),
        p_listing_ids: mappings.map((item) => item.listing_id),
      })
      if (reconciled.error) return Response.json({ error: 'Intake event Listing ID reconciliation failed' }, { status: 500 })
      listingIdsReconciled = Number(reconciled.data ?? 0)
    }
    const missing = missingActivePageRows(activeIds, current.data ?? []).map((row: { listing_id: string }) => row.listing_id)
    if (missing.length) {
      const deletedAt = new Date().toISOString()
      const updated = await supabase.from('crm_inventory_snapshot').update({ deleted_at: deletedAt, last_synced_at: deletedAt })
        .in('listing_id', missing)
      if (updated.error) return Response.json({ error: 'Missing Notion inventory rows could not be soft-deleted' }, { status: 500 })
    }
    console.info('Notion inventory reconciliation completed', { active_pages: activeIds.length, checked_rows: current.data?.length ?? 0, listing_ids_reconciled: listingIdsReconciled, soft_deleted: missing.length })
    return Response.json({ ok: true, active_pages: activeIds.length, checked_rows: current.data?.length ?? 0, listing_ids_reconciled: listingIdsReconciled, soft_deleted: missing.length })
  } else if (operation === 'sync_inventory') {
    const listingId = String(body.listing_id ?? '').trim()
    const row = body.row
    if (!/^EF-\d{4}-[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{4}$/.test(listingId) || !row || typeof row !== 'object' || Array.isArray(row)) {
      return Response.json({ error: 'Invalid inventory row' }, { status: 400 })
    }
    const record = row as Record<string, unknown>
    const sourceHash = String(body.source_hash ?? '')
    if (!/^[a-f0-9]{64}$/i.test(sourceHash) || String(record.listing_id ?? '') !== listingId) {
      return Response.json({ error: 'Invalid inventory identity or hash' }, { status: 400 })
    }
    const numeric = (value: unknown) => {
      if (value === null || value === undefined || value === '') return null
      const n = Number(value)
      return Number.isFinite(n) ? n : null
    }
    const urls = String(record.cloudinary_image_urls ?? '').split(',').map((x) => x.trim()).filter(Boolean)
    const result = await supabase.from('crm_inventory_snapshot').upsert({
      listing_id: listingId,
      source_kind: 'housing_notion',
      source_tab: 'Housing Listings',
      locality: String(record.locality ?? ''),
      society_name: String(record.society_name ?? ''),
      bhk: String(record.BHK ?? ''),
      monthly_rent: numeric(record.monthly_rent),
      furnishing: String(record.furnish_type ?? ''),
      listing_state: String(record.listing_state ?? 'Unknown'),
      intake_status: String(record.intake_status ?? ''),
      pet_friendly: String(record.pet_friendly ?? ''),
      cloudinary_image_urls: urls,
      source_snapshot_at: new Date().toISOString(),
      last_synced_at: new Date().toISOString(),
      source_record: record,
      source_hash: sourceHash,
      deleted_at: body.deleted === true ? new Date().toISOString() : null,
    }, { onConflict: 'listing_id' })
    if (result.error) {
      console.error('Notion inventory projection failed', { code: result.error.code })
      return Response.json({ error: 'Inventory projection failed' }, { status: 500 })
    }
    return Response.json({ ok: true, listing_id: listingId })
  } else {
    return Response.json({ error: 'Unsupported operation' }, { status: 400 })
  }
  if (result.error) {
    console.error('Notion inventory state operation failed', { operation, code: result.error.code })
    return Response.json({ error: 'Inventory state operation failed' }, { status: 500 })
  }
  return Response.json(responseForOperation(operation, result.data))
})
