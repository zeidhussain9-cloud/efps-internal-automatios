import test from 'node:test';
import assert from 'node:assert/strict';
import {buildCrmPath,CRM_LEAD_TAB_PATHS,CRM_PAGE_PATHS,parseCrmPath} from '../src/crm-ui-routes.mjs';

test('every primary CRM screen has a stable direct route',()=>{
 for(const [page,path] of Object.entries(CRM_PAGE_PATHS)){
  assert.deepEqual(parseCrmPath(path),{page,leadId:null,tab:'Overview',notFound:false,isRoot:false});
 }
 assert.deepEqual(parseCrmPath('/'),{page:'Dashboard',leadId:null,tab:'Overview',notFound:false,isRoot:true});
 assert.deepEqual(parseCrmPath('/inventory/'),{page:'Inventory',leadId:null,tab:'Overview',notFound:false,isRoot:false});
});

test('lead workspace deep links preserve the lead ID and selected tab',()=>{
 for(const [tab,slug] of Object.entries(CRM_LEAD_TAB_PATHS)){
  const path=buildCrmPath({page:'Leads Inbox',leadId:'lead-123',tab});
  assert.equal(path,'/leads/lead-123/'+slug);
  assert.deepEqual(parseCrmPath(path),{page:'Leads Inbox',leadId:'lead-123',tab,notFound:false,isRoot:false});
 }
 assert.deepEqual(parseCrmPath('/leads/lead-123'),{page:'Leads Inbox',leadId:'lead-123',tab:'Overview',notFound:false,isRoot:false});
});

test('lead IDs are URI-encoded, bounded, and cannot inject path segments',()=>{
 assert.equal(buildCrmPath({page:'Leads Inbox',leadId:'customer id',tab:'Overview'}),'/leads/customer%20id/overview');
 assert.equal(parseCrmPath('/leads/customer%20id/overview').leadId,'customer id');
 for(const id of ['', '.', '..', 'x/y', 'x\\y', 'x'.repeat(129)]){
  assert.throws(()=>buildCrmPath({page:'Leads Inbox',leadId:id}),/Invalid lead route identifier/);
 }
 assert.equal(parseCrmPath('/leads/x%2Fy/overview').notFound,true);
 assert.equal(parseCrmPath('/leads/%E0%A4%A/overview').notFound,true);
});

test('unknown and malformed routes resolve to an explicit not-found state',()=>{
 for(const path of ['/missing','/leads/LIVE-1/unknown','//leads/LIVE-1/child','/activity/child']){
  assert.deepEqual(parseCrmPath(path),{page:'Not Found',leadId:null,tab:'Overview',notFound:true,isRoot:false});
 }
});

test('route builder rejects unsupported screen and workspace combinations',()=>{
 assert.throws(()=>buildCrmPath({page:'Unknown'}),/Unknown CRM page/);
 assert.throws(()=>buildCrmPath({page:'Dashboard',leadId:'lead-1'}),/requires the Leads Inbox/);
 assert.throws(()=>buildCrmPath({page:'Leads Inbox',leadId:'lead-1',tab:'Unknown'}),/Unknown lead workspace tab/);
});