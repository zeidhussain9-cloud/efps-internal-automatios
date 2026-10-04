const MCP_URL=String(process.env.CRM_SOURCE_AUDIT_URL||'https://easyfind-crm-d01-d05.onrender.com/mcp').trim();
const TOKEN=String(process.env.CRM_SOURCE_AUDIT_TOKEN||'').trim();

if(!TOKEN) throw new Error('CRM_SOURCE_AUDIT_TOKEN is required');
const parsedUrl=new URL(MCP_URL);
if(parsedUrl.protocol!=='https:'&&!['localhost','127.0.0.1'].includes(parsedUrl.hostname)) throw new Error('CRM_SOURCE_AUDIT_URL must use HTTPS');

async function callMcp(id,method,params={}){
  const response=await fetch(MCP_URL,{
    method:'POST',
    headers:{
      Authorization:'Bearer '+TOKEN,
      'Content-Type':'application/json',
      Accept:'application/json, text/event-stream'
    },
    body:JSON.stringify({jsonrpc:'2.0',id,method,params})
  });
  const body=await response.text();
  if(!response.ok) throw new Error(`MCP HTTP ${response.status}: ${body.slice(0,500)}`);
  return parseMcpBody(body);
}

function parseMcpBody(body){
  const trimmed=body.trim();
  if(!trimmed) throw new Error('MCP returned an empty response');
  if(trimmed.startsWith('{')) return JSON.parse(trimmed);
  const dataLines=trimmed.split(/\r?\n/).filter(line=>line.startsWith('data:')).map(line=>line.slice(5).trim()).filter(Boolean);
  if(!dataLines.length) throw new Error('MCP response did not contain JSON data');
  return JSON.parse(dataLines[dataLines.length-1]);
}

const init=await callMcp(1,'initialize',{
  protocolVersion:'2025-11-25',
  capabilities:{},
  clientInfo:{name:'efps-crm-schedule-runner',version:'1.0.0'}
});
if(init.error) throw new Error(`MCP initialize failed: ${init.error.message||'unknown error'}`);

const result=await callMcp(2,'tools/call',{
  name:'crm_source_audit_snapshot',
  arguments:{}
});
if(result.error) throw new Error(`Source audit failed: ${result.error.message||'unknown error'}`);

const content=result.result?.content;
if(!Array.isArray(content)||content.length===0) throw new Error('Source audit returned no content');
const payload=JSON.parse(String(content[0]?.text||''));
if(!payload||typeof payload!=='object') throw new Error('Source audit returned an invalid payload');

const failures=[];
for(const [name,value] of Object.entries(payload)){
  if(value&&typeof value==='object'&&value.error) failures.push(`${name}: ${value.error}`);
}
if(payload.catalog?.complete!==true) failures.push('catalog: incomplete catalog reconciliation');
if(payload.sheet?.availableCatalogCount!==undefined&&payload.catalog?.productCount!==undefined&&Number(payload.sheet.availableCatalogCount)!==Number(payload.catalog.productCount)){
  failures.push(`catalog count mismatch: Sheet available=${payload.sheet.availableCatalogCount}, WhAPI products=${payload.catalog.productCount}`);
}
if(failures.length) throw new Error('Source audit failures: '+failures.join('; ')+' | whapi='+JSON.stringify(payload.whapi)+' | sheet='+JSON.stringify(payload.sheet)+' | catalog='+JSON.stringify(payload.catalog));

console.log(JSON.stringify({
  ok:true,
  checked_at:new Date().toISOString(),
  source_audit:payload,
  catalog_reconciliation:{
    sheet_available:Number(payload.sheet.availableCatalogCount),
    whapi_products:Number(payload.catalog.productCount),
    matched:Number(payload.sheet.availableCatalogCount)===Number(payload.catalog.productCount),
    products_with_collections:Number(payload.catalog.productsWithCollections),
    products_without_collections:Number(payload.catalog.productsWithoutCollections)
  }
},null,2));
