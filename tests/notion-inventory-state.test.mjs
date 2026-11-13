import test from 'node:test'
import assert from 'node:assert/strict'
import { missingActivePageRows, responseForOperation } from '../supabase/functions/notion-inventory-state/response-contract.mjs'

test('Notion claim response preserves the full claim result', () => {
  const claim = { status: 'claimed', item: { listing_id: '' } }
  assert.deepEqual(responseForOperation('claim', claim), claim)
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
