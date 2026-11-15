import test from 'node:test'
import assert from 'node:assert/strict'
import { v5Projection,effectiveInventoryState,mayDistribute } from '../supabase/functions/notion-inventory-state/inventory-v5-contract.mjs'

test('legacy projection does not require additive SQL columns',()=>{
 assert.deepEqual(v5Projection({listing_state:'Available'}),{})
 assert.deepEqual(effectiveInventoryState({listing_state:'Available'}),{availability:'Available',pipeline:null,liveOn:null})
 assert.equal(mayDistribute({listing_state:'Available'}),false)
})
test('v5 retains typed channel arrays and qualified instant',()=>{
 const r={inventory_contract_version:5,Availability:'Available','Pipeline Status':'Ready to Post','Live On':['Meta Catalogue'],onboarded_at:'2026-11-15T14:30:00+05:30'}
 assert.deepEqual(v5Projection(r),{availability:'Available',pipeline_status:'Ready to Post',live_on:['Meta Catalogue'],onboarded_at:r.onboarded_at,inventory_contract_version:5})
 assert.equal(mayDistribute({...v5Projection(r)}),true)
 assert.equal(mayDistribute({...v5Projection(r),availability:'On Hold'}),false)
})
test('v5 rejects flattened/duplicate/unknown channels and unqualified dates',()=>{
 const r={inventory_contract_version:5,Availability:'Rented Out','Pipeline Status':'Removed','Live On':[]}
 for(const value of ['Meta Catalogue',['Unknown'],['Meta Catalogue','Meta Catalogue'],null]) assert.throws(()=>v5Projection({...r,'Live On':value}))
 for(const value of ['2026-11-15','Sunday, November 15, 2026 at 02:30:00 pm','invalid']) assert.throws(()=>v5Projection({...r,onboarded_at:value}))
 assert.deepEqual(v5Projection(r).live_on,[])
})
