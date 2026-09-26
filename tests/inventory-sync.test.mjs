import test from 'node:test';
import assert from 'node:assert/strict';
import {diffInventory,projectSheetRows} from '../src/inventory-sync.mjs';
test('projects canonical Sheet rows and rejects duplicate IDs',()=>{
 const header=[];assert.deepEqual(projectSheetRows([]),[]);
 const row=[];row[0]='EF-2609-TEST';row[7]='Whitefield';row[13]='2 BHK';row[20]='50000';row[34]='https://res.cloudinary.com/x/image/upload/a.jpg, https://res.cloudinary.com/x/image/upload/b.jpg';
 const out=projectSheetRows([row]);assert.equal(out.length,1);assert.equal(out[0].row.locality,'Whitefield');assert.equal(out[0].row.cloudinary_image_urls.length,2);assert.equal(out[0].row.listing_id,'EF-2609-TEST');
 assert.throws(()=>projectSheetRows([row,row]),/Duplicate listing_id/);
});
test('full reconciliation detects changed and removed Sheet rows',()=>{
 const existing=new Map([['A',{source_kind:'housing_sheet',source_hash:'old',deleted_at:null}],['B',{source_kind:'housing_sheet',source_hash:'same',deleted_at:null}],['C',{source_kind:'synthetic',source_hash:'x',deleted_at:null}]]);
 const incoming=[{row:{listing_id:'A'},sourceHash:'new'},{row:{listing_id:'B'},sourceHash:'same'}];
 assert.deepEqual(diffInventory(existing,incoming),{changed:1,removed:0,total:2});
 const incoming2=[{row:{listing_id:'A'},sourceHash:'new'}];
 assert.deepEqual(diffInventory(existing,incoming2),{changed:1,removed:1,total:1});
});
