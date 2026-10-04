import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {reconcileCatalogProducts} from '../src/crm-source-audit.mjs';

test('catalog reconciliation counts assigned and unassigned products deterministically',()=>{
  const result=reconcileCatalogProducts(
    [{id:'p1'},{id:'p2'},{id:'p3'}],
    [{id:'c1',products:[{id:'p1'},{id:'p2'}]},{id:'c2',products:[{id:'p2'}]}]
  );
  assert.deepEqual(result,{productCount:3,productsWithCollections:2,productsWithoutCollections:1});
});

test('source audit MCP exposes only read-only audit tools',async()=>{
  process.env.CRM_SOURCE_AUDIT_MCP_ENABLED='true';
  process.env.CRM_SOURCE_AUDIT_TOKEN='test-token';
  const {handleAuditMcp}=await import('../audit-mcp-server.mjs');
  const server=createServer((req,res)=>handleAuditMcp(req,res));
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const port=server.address().port;
  try{
    const init=await fetch(`http://127.0.0.1:${port}/mcp`,{method:'POST',headers:{Authorization:'Bearer test-token','Content-Type':'application/json','Accept':'application/json, text/event-stream'},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-11-25',capabilities:{},clientInfo:{name:'test',version:'1'}}})});
    assert.equal(init.status,200);
    const list=await fetch(`http://127.0.0.1:${port}/mcp`,{method:'POST',headers:{Authorization:'Bearer test-token','Content-Type':'application/json','Accept':'application/json, text/event-stream'},body:JSON.stringify({jsonrpc:'2.0',id:2,method:'tools/list',params:{}})});
    assert.equal(list.status,200);
    const text=await list.text();
    assert.match(text,/whapi_channel_health/); assert.match(text,/whapi_catalog_audit/); assert.match(text,/google_housing_sheet_snapshot/); assert.match(text,/crm_source_audit_snapshot/);
    assert.doesNotMatch(text,/send_text|create_product|edit_collection/);
    const denied=await fetch(`http://127.0.0.1:${port}/mcp`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    assert.equal(denied.status,401);
  } finally {await new Promise(resolve=>server.close(resolve));}
});
