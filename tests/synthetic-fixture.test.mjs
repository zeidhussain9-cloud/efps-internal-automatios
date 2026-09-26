import test from 'node:test';import assert from 'node:assert/strict';import {customers,inventory,efpsSources,assertSyntheticFixture} from './fixtures/synthetic-pilot.mjs';
test('fixture identifiers and source attribution are valid',()=>assert.equal(assertSyntheticFixture(),true));
test('fictional customer phones never equal verified EFPS source numbers',()=>{for(const c of customers){assert.ok(!efpsSources.includes(c.phone));assert.ok(efpsSources.includes(c.source));}});
test('expected extraction has explicit unknown budget',()=>{assert.equal(customers[2].expected.budgetMax,null);assert.equal(customers[1].expected.budgetMax,32000);});
test('fixture inventory images never imply unrelated photos',()=>{for(const p of inventory)assert.deepEqual(p.cloudinary_image_urls,[]);});
test('unavailable property cannot be suggested as available',()=>{assert.equal(inventory.find(p=>p.listing_id==='TEST-P003').listing_state,'Rented Out');});
test('conversation fixture has unique source message IDs',()=>{const ids=customers.flatMap(c=>c.messages.map(m=>m.id));assert.equal(new Set(ids).size,ids.length);});
