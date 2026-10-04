import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';

test('schedule runner fails closed without its audit token',async()=>{
  const previous=process.env.CRM_SOURCE_AUDIT_TOKEN;
  delete process.env.CRM_SOURCE_AUDIT_TOKEN;
  await assert.rejects(
    import('../scripts/crm-source-audit-runner.mjs?missing-token-test'),
    /CRM_SOURCE_AUDIT_TOKEN is required/
  );
  if(previous===undefined) delete process.env.CRM_SOURCE_AUDIT_TOKEN;
  else process.env.CRM_SOURCE_AUDIT_TOKEN=previous;
});

test('schedule runner calls the read-only source audit tool',async()=>{
  const previousToken=process.env.CRM_SOURCE_AUDIT_TOKEN;
  const previousUrl=process.env.CRM_SOURCE_AUDIT_URL;
  process.env.CRM_SOURCE_AUDIT_TOKEN='test-token';
  const server=createServer(async(req,res)=>{
    assert.equal(req.url,'/mcp');
    assert.equal(req.headers.authorization,'Bearer test-token');
    const body=JSON.parse(await new Promise((resolve,reject)=>{
      let raw='';req.on('data',chunk=>raw+=chunk);req.on('end',()=>resolve(raw));req.on('error',reject);
    }));
    res.writeHead(200,{'Content-Type':'application/json'});
    if(body.method==='initialize') return res.end(JSON.stringify({jsonrpc:'2.0',id:body.id,result:{protocolVersion:'2025-11-25'}}));
    if(body.method==='tools/call') return res.end(JSON.stringify({jsonrpc:'2.0',id:body.id,result:{content:[{type:'text',text:JSON.stringify({whapi:{ok:true},sheet:{ok:true},crm:{ok:true}})}]}}));
    res.end(JSON.stringify({jsonrpc:'2.0',id:body.id,result:{}}));
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const port=server.address().port;
  process.env.CRM_SOURCE_AUDIT_URL=`http://127.0.0.1:${port}/mcp`;
  const output=[];
  const originalLog=console.log;
  console.log=(...args)=>output.push(args.join(' '));
  try{
    await import('../scripts/crm-source-audit-runner.mjs?happy-path-test');
    assert.match(output.join(' '),/"ok": true/);
    assert.match(output.join(' '),/"whapi"/);
  }finally{
    console.log=originalLog;
    await new Promise(resolve=>server.close(resolve));
    if(previousToken===undefined) delete process.env.CRM_SOURCE_AUDIT_TOKEN;
    else process.env.CRM_SOURCE_AUDIT_TOKEN=previousToken;
    if(previousUrl===undefined) delete process.env.CRM_SOURCE_AUDIT_URL;
    else process.env.CRM_SOURCE_AUDIT_URL=previousUrl;
  }
});
