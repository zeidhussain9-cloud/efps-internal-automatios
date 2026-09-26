import test from 'node:test';import assert from 'node:assert/strict';import{spawn}from 'node:child_process';
async function start(extra={}){const port=20000+Math.floor(Math.random()*10000),base='http://127.0.0.1:'+port;const proc=spawn(process.execPath,['crm-server.mjs'],{env:{...process.env,PORT:String(port),CRM_BASIC_AUTH_USERNAME:'',CRM_BASIC_AUTH_PASSWORD:'',CRM_SYNTHETIC_AI_ENABLED:'',...extra},stdio:['ignore','pipe','pipe']});let stdout='',stderr='';proc.stdout.on('data',b=>{stdout+=b.toString()});proc.stderr.on('data',b=>{stderr+=b.toString()});for(let i=0;i<40;i++){try{const r=await fetch(base+'/health');if(r.ok)return{proc,base}}catch{}if(proc.exitCode!==null)break;await new Promise(resolve=>setTimeout(resolve,100))}const detail=(stderr||stdout).replace(/\b(postgres(?:ql)?:\/\/)[^\s]+/gi,'$1[redacted]').slice(0,1000);proc.kill();throw Error('Server failed to start (exit='+proc.exitCode+', detail='+detail+')')}
test('server access gate blocks unauthenticated content and fictional AI',async()=>{const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'fictional-secret'});try{const health=await fetch(base+'/health');assert.equal(health.status,200);const headers=health.headers;assert.equal(headers.get('x-content-type-options'),'nosniff');assert.equal(headers.get('x-frame-options'),'DENY');assert.equal(headers.get('strict-transport-security'),'max-age=31536000');const healthBody=await health.json();assert.deepEqual(healthBody,{ok:true});const no=await fetch(base+'/');assert.equal(no.status,401);const yes=await fetch(base+'/',{headers:{Authorization:'Basic '+Buffer.from('pilot:fictional-secret').toString('base64')}});assert.equal(yes.status,200);const ai=await fetch(base+'/api/ai/analyze',{method:'POST',headers:{Authorization:'Basic '+Buffer.from('pilot:fictional-secret').toString('base64'),'Content-Type':'application/json'},body:JSON.stringify({leadId:'L-1001'})});assert.equal(ai.status,403)}finally{proc.kill()}});
test('incomplete auth configuration fails closed',async()=>{const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot'});try{assert.equal((await fetch(base+'/')).status,503)}finally{proc.kill()}});
test('unknown APIs and traversal cannot expose files',async()=>{const{proc,base}=await start();try{assert.equal((await fetch(base+'/api/private')).status,404);assert.equal((await fetch(base+'/missing.js')).status,404);assert.equal((await fetch(base+'/',{method:'PUT'})).status,405)}finally{proc.kill()}});

test('database pilot routes fail closed without opt-in and connection',async()=>{const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'fictional-secret',CRM_DB_READ_ENABLED:'true',DATABASE_URL:''});try{const auth='Basic '+Buffer.from('pilot:fictional-secret').toString('base64');assert.equal((await fetch(base+'/api/db/status')).status,401);assert.equal((await fetch(base+'/api/db/status',{headers:{Authorization:auth}})).status,404);assert.equal((await fetch(base+'/api/db/leads',{headers:{Authorization:auth}})).status,404)}finally{proc.kill()}});

test('durable DB mutations remain fail-closed until write gate is enabled',async()=>{
 const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'fictional-secret',CRM_DB_WRITE_ENABLED:'true',DATABASE_URL:''});
 try{
  const auth='Basic '+Buffer.from('pilot:fictional-secret').toString('base64');
  const response=await fetch(base+'/api/db/leads',{method:'POST',headers:{Authorization:auth,'Content-Type':'application/json'},body:JSON.stringify({id:'L-1001'})});
  assert.equal(response.status,404);
 }finally{proc.kill()}
});
test('write gate does not shadow GET lead routes',async()=>{
 const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'fictional-secret',CRM_DB_WRITE_ENABLED:'true',CRM_DB_READ_ENABLED:'true',DATABASE_URL:''});
 try{
  const auth='Basic '+Buffer.from('pilot:fictional-secret').toString('base64');
  const response=await fetch(base+'/api/db/leads',{headers:{Authorization:auth}});
  assert.equal(response.status,404);
 }finally{proc.kill()}
});

test('authenticated fictional AI route reaches Ollama-compatible provider without accepting real leads',async()=>{
 const {createServer}=await import('node:http');
 let requests=0;
 const provider=createServer(async(req,res)=>{requests++;assert.equal(req.url,'/api/chat');assert.equal(req.headers.authorization,'Bearer synthetic-provider-key');let body='';for await(const chunk of req)body+=chunk;const data=JSON.parse(body);assert.equal(data.stream,false);assert.equal(data.model,'test-model');assert.match(data.messages[1].content,/Fictional renter/);res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({message:{content:JSON.stringify({bhk:2,location:'Harlur',budget:52000,pets:'preferred',uncertainties:[]})}}))});
 await new Promise(resolve=>provider.listen(0,'127.0.0.1',resolve));
 const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'fictional-secret',CRM_SYNTHETIC_AI_ENABLED:'true',OLLAMA_BASE_URL:'http://127.0.0.1:'+provider.address().port,OLLAMA_MODEL:'test-model',OLLAMA_API_KEY:'synthetic-provider-key'});
 try{
  const auth='Basic '+Buffer.from('pilot:fictional-secret').toString('base64');
  const request=leadId=>fetch(base+'/api/ai/analyze',{method:'POST',headers:{Authorization:auth,'Content-Type':'application/json'},body:JSON.stringify({leadId})});
  assert.equal((await fetch(base+'/api/ai/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({leadId:'L-1001'})})).status,401);
  const rejected=await request('real-customer');assert.equal(rejected.status,422);assert.equal(requests,0);
  const response=await request('L-1001');assert.equal(response.status,200);const result=await response.json();assert.equal(result.fictional,true);assert.equal(result.proposal.budget,52000);assert.equal(requests,1);
 }finally{proc.kill();await new Promise(resolve=>provider.close(resolve))}
});
