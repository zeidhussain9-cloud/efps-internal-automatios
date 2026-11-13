import test from 'node:test'
import assert from 'node:assert/strict'
import { responseForOperation } from '../supabase/functions/notion-inventory-state/response-contract.mjs'

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
