import test from 'node:test'
import assert from 'node:assert/strict'
import { missingActivePageRows, responseForOperation } from '../supabase/functions/notion-inventory-state/response-contract.mjs'

test('Notion claim response preserves the full claim result', () => {
  const claim = { status: 'claimed', item: { listing_id: '' } }
  assert.deepEqual(responseForOperation('claim', claim), claim)
})

test('Notion webhook event receipt returns the durable event identity and enqueue decision', () => {
  const event = { id: '32345678-1234-4234-8234-123456789abc', status: 'accepted', should_enqueue: true, duplicate: false }
  assert.deepEqual(responseForOperation('record_webhook_event', event), event)
})

test('Notion webhook event lifecycle updates return the persisted transition result', () => {
  const update = { ok: true, id: '32345678-1234-4234-8234-123456789abc', status: 'processed', started: false }
  assert.deepEqual(responseForOperation('update_webhook_event', update), update)
})

test('Notion Listing ID allocation returns the ID expected by the Lambda', () => {
  assert.deepEqual(responseForOperation('allocate_listing_id', 'EF-2611-ABCD'), { listing_id: 'EF-2611-ABCD' })
})

test('other Notion state operations retain the acknowledgement response', () => {
  assert.deepEqual(responseForOperation('finish', undefined), { ok: true })
})

test('Notion reconciliation identifies only missing active page projections', () => {
  const rows = [
    { listing_id: 'EF-2611-AAAA', source_record: { notion_page_id: 'page-a' } },
    { listing_id: 'EF-2611-BBBB', source_record: { notion_page_id: 'page-b' } },
    { listing_id: 'EF-2611-CCCC', source_record: { notion_page_id: 'page-c' } },
    { listing_id: 'EF-2611-DDDD', source_record: {} },
  ]
  assert.deepEqual(missingActivePageRows(['PAGE-A', 'page-c'], rows).map((row) => row.listing_id), ['EF-2611-BBBB', 'EF-2611-DDDD'])
})
