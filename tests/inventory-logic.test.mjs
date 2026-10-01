import test from 'node:test';
import assert from 'node:assert/strict';
import {INVENTORY_PAGE_SIZE,INVENTORY_SORT_OPTIONS,buildInventoryPage,normalizeInventorySort,sortInventoryRows} from '../src/inventory-logic.mjs';

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

test('inventory filters, sorting, summaries, facets, and pages compose on the server',()=>{
 const source=rows.map((row,index)=>({...row,listing_state:index===1?'Rented Out':'Available',cloudinary_image_urls:index!==1?['https://images.example/property.jpg']:[],source_record:{catalog_title:'Bengaluru home'}}));
 const page=buildInventoryPage(source,{limit:1,offset:1,sort:'rent_asc',status:'Available',withPhotos:true,search:'home'},row=>row.cloudinary_image_urls.length>0);
 assert.equal(page.total,2);
 assert.equal(page.limit,1);
 assert.equal(page.offset,1);
 assert.equal(page.hasMore,false);
 assert.deepEqual(page.rows.map(row=>row.listing_id),['INV-3']);
 assert.deepEqual(page.summary,{total:3,available:2,rented:1,withPhotos:2,statusCounts:{Available:2,'Rented Out':1}});
 assert.deepEqual(page.facets.statuses,['Available','Rented Out']);
 assert.equal(INVENTORY_PAGE_SIZE,24);
});

test('inventory pagination rejects invalid limits and offsets',()=>{
 assert.throws(()=>buildInventoryPage(rows,{limit:0,offset:0}),/Invalid inventory pagination/);
 assert.throws(()=>buildInventoryPage(rows,{limit:24,offset:-1}),/Invalid inventory pagination/);
});
