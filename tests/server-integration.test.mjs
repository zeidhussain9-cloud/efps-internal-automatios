import test from 'node:test';import assert from 'node:assert/strict';import{spawn}from 'node:child_process';
async function start(extra={}){const port=20000+Math.floor(Math.random()*10000),base='http://127.0.0.1:'+port;const proc=spawn(process.execPath,['crm-server.mjs'],{env:{...process.env,PORT:String(port),CRM_BASIC_AUTH_USERNAME:'',CRM_BASIC_AUTH_PASSWORD:'',CRM_SYNTHETIC_AI_ENABLED:'',...extra},stdio:['ignore','pipe','pipe']});let stdout='',stderr='';proc.stdout.on('data',b=>{stdout+=b.toString()});proc.stderr.on('data',b=>{stderr+=b.toString()});for(let i=0;i<40;i++){try{const r=await fetch(base+'/health');if(r.ok)return{proc,base}}catch{}if(proc.exitCode!==null)break;await new Promise(resolve=>setTimeout(resolve,100))}const detail=(stderr||stdout).replace(/\b(postgres(?:ql)?:\/\/)[^\s]+/gi,'$1[redacted]').slice(0,1000);proc.kill();throw Error('Server failed to start (exit='+proc.exitCode+', detail='+detail+')')}
test('server access gate blocks unauthenticated content and retired synthetic AI',async()=>{const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'fictional-secret'});try{const health=await fetch(base+'/health');assert.equal(health.status,200);const headers=health.headers;assert.equal(headers.get('x-content-type-options'),'nosniff');assert.equal(headers.get('x-frame-options'),'DENY');assert.equal(headers.get('strict-transport-security'),'max-age=31536000');const healthBody=await health.json();assert.deepEqual(healthBody,{ok:true});const no=await fetch(base+'/');assert.equal(no.status,200);const yes=await fetch(base+'/',{headers:{Authorization:'Basic '+Buffer.from('pilot:fictional-secret').toString('base64')}});assert.equal(yes.status,200);const ai=await fetch(base+'/api/ai/analyze',{method:'POST',headers:{Authorization:'Basic '+Buffer.from('pilot:fictional-secret').toString('base64'),'Content-Type':'application/json'},body:JSON.stringify({leadId:'L-1001'})});assert.equal(ai.status,404)}finally{proc.kill()}});
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


test('Render no longer accepts WhatsApp webhook writes',async()=>{const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'fictional-secret'});try{const auth='Basic '+Buffer.from('pilot:fictional-secret').toString('base64');const response=await fetch(base+'/api/webhooks/whatsapp',{method:'POST',headers:{Authorization:auth,'Content-Type':'application/json'},body:'{}'});assert.equal(response.status,405)}finally{proc.kill()}});

test('operator session login, logout and cross-origin protection',async()=>{
 const{proc,base}=await start({CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'test-pass'});
 try{
  const initial=await fetch(base+'/api/auth/session');assert.equal(initial.status,200);assert.equal((await initial.json()).authenticated,false);
  const denied=await fetch(base+'/api/db/status');assert.equal(denied.status,401);
  const bad=await fetch(base+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json',Origin:base},body:JSON.stringify({username:'pilot',password:'wrong'})});assert.equal(bad.status,401);
  const login=await fetch(base+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json',Origin:base},body:JSON.stringify({username:'pilot',password:'test-pass'})});assert.equal(login.status,200);const cookie=login.headers.get('set-cookie');assert.ok(cookie.includes('efps_crm_session='));
  const foreign=await fetch(base+'/api/auth/logout',{method:'POST',headers:{Cookie:cookie,Origin:'https://evil.example'}});assert.equal(foreign.status,403);
  const local=await fetch(base+'/api/auth/logout',{method:'POST',headers:{Cookie:cookie,Origin:base}});assert.equal(local.status,204);
  const after=await fetch(base+'/api/auth/session',{headers:{Cookie:cookie}});assert.equal((await after.json()).authenticated,false);
 }finally{proc.kill()}
});
