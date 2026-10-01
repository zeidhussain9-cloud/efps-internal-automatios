import test from 'node:test';
import assert from 'node:assert/strict';
import {INVENTORY_SORT_OPTIONS,normalizeInventorySort,sortInventoryRows} from '../src/inventory-logic.mjs';

const rows=[
 {listing_id:'INV-3',bhk:'3 BHK',monthly_rent:70000,locality:'Sarjapur',onboarded_on:'30 Sep 2026, 8:00 AM'},
 {listing_id:'INV-1',bhk:'1 BHK',monthly_rent:22000,locality:'Bellandur',onboarded_on:'25 Sep 2026, 8:00 AM'},
 {listing_id:'INV-2',bhk:'2 BHK',monthly_rent:45000,locality:'Harlur',onboarded_on:'28 Sep 2026, 8:00 AM'},
];

test('inventory exposes stable sort options including latest and oldest',()=>{
 assert.deepEqual(INVENTORY_SORT_OPTIONS.slice(0,2),[['latest','Latest'],['oldest','Oldest']]);
 assert.equal(normalizeInventorySort('latest'),'latest');
 assert.equal(normalizeInventorySort('invalid'),'latest');
});

test('inventory sort is deterministic for chronology, rent, BHK and locality',()=>{
 assert.deepEqual(sortInventoryRows(rows,'latest').map(r=>r.listing_id),['INV-3','INV-2','INV-1']);
 assert.deepEqual(sortInventoryRows(rows,'oldest').map(r=>r.listing_id),['INV-1','INV-2','INV-3']);
 assert.deepEqual(sortInventoryRows(rows,'rent_asc').map(r=>r.listing_id),['INV-1','INV-2','INV-3']);
 assert.deepEqual(sortInventoryRows(rows,'rent_desc').map(r=>r.listing_id),['INV-3','INV-2','INV-1']);
 assert.deepEqual(sortInventoryRows(rows,'bhk_asc').map(r=>r.listing_id),['INV-1','INV-2','INV-3']);
 assert.deepEqual(sortInventoryRows(rows,'bhk_desc').map(r=>r.listing_id),['INV-3','INV-2','INV-1']);
 assert.deepEqual(sortInventoryRows(rows,'locality_asc').map(r=>r.listing_id),['INV-1','INV-2','INV-3']);
});
