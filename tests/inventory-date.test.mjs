import test from 'node:test';import assert from'node:assert/strict';import{inventoryInstant}from'../src/inventory-date.mjs';import{sortInventoryRows}from'../src/inventory-logic.mjs';
test('legacy readable timestamps have explicit India offset independent of machine zone',()=>{
 assert.equal(inventoryInstant('Sunday, November 15, 2026 at 02:41:00 pm'),Date.parse('2026-11-15T09:11:00Z'));
 assert.equal(inventoryInstant('15 Nov 2026, 2:41 PM'),Date.parse('2026-11-15T09:11:00Z'));
 assert.equal(inventoryInstant('15 Nov 2026, 12:15 AM'),Date.parse('2026-11-14T18:45:00Z'));
});
test('bad weekdays, calendar overflows, and unqualified dates never guessed',()=>{
 for(const x of ['Monday, November 15, 2026 at 02:41:00 pm','Sunday, November 31, 2026 at 02:41:00 pm','31 Feb 2026, 8:00 AM','2026-11-15','2026-11-15T09:11:00',''])assert.equal(inventoryInstant(x),null,x);
});
test('internal onboarding instant beats display and mirror update time',()=>{
 const rows=[{listing_id:'new',onboarded_at:'2026-11-15T09:11:00Z',onboarded_on:'15 Nov 2026, 2:41 PM'},{listing_id:'old',onboarded_at:'2026-11-14T09:11:00Z',last_synced_at:'2026-12-15T09:11:00Z'}];
 assert.deepEqual(sortInventoryRows(rows,'latest').map(x=>x.listing_id),['new','old']);
});
