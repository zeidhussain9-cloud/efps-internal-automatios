import test from 'node:test';
import assert from 'node:assert/strict';
import {diffInventory,inventoryChangeRows,projectSheetRows} from '../src/inventory-sync.mjs';
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

test('reserved AU/AV columns never enter the operational CRM projection',()=>{
 const row=[];row[0]='RESERVED-1';row[45]='AT-value';row[46]='legacy-source-group';row[47]='Yes';
 const out=projectSheetRows([row])[0].row;
 assert.equal(out.meta_catalog_status,'AT-value');
 assert.equal(out.source_group,'');
 assert.equal(out.inventory_locked,'');
});
test('inventory change history reconstructs create, field edit and delete',()=>{
 const incoming1=projectSheetRows([Object.assign([], {0:'RT-1',7:'Whitefield',13:'2 BHK',20:'50000'})]);
 const created=inventoryChangeRows(new Map(),incoming1,'run-1','2026-10-01T00:00:00Z');
 assert.equal(created.length,1);assert.equal(created[0].change_type,'created');
 const old=new Map([['RT-1',{source_kind:'housing_sheet',source_hash:incoming1[0].sourceHash,source_record:incoming1[0].row,deleted_at:null}],['RT-2',{source_kind:'housing_sheet',source_hash:'old-2',source_record:{listing_id:'RT-2',locality:'Old'},deleted_at:null}]]);
 const editedRow=Object.assign([], {0:'RT-1',7:'Indiranagar',13:'2 BHK',20:'50000'});
 const incoming2=projectSheetRows([editedRow]);
 const edited=inventoryChangeRows(old,incoming2,'run-2','2026-10-01T00:05:00Z');
 assert.ok(edited.some(x=>x.listing_id==='RT-1'&&x.field_name==='locality'&&x.old_value==='Whitefield'&&x.new_value==='Indiranagar'));
 assert.ok(edited.some(x=>x.listing_id==='RT-2'&&x.change_type==='deleted'));
});
