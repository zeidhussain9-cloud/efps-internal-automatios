import test from 'node:test';
import assert from 'node:assert/strict';
import {configurationStatus,startupDatabaseCheck} from '../src/crm-startup-check.mjs';
import {connectionStringShape} from '../src/crm-repository.mjs';
test('reports presence only, not credential contents',()=>{
 const f=configurationStatus({DATABASE_URL:'postgres://private',CRM_BASIC_AUTH_USERNAME:'operator',CRM_BASIC_AUTH_PASSWORD:'private-password',CRM_DB_READ_ENABLED:'true',OLLAMA_HOST:'https://private',OLLAMA_MODEL:'model'});
 assert.equal(f.databaseUrlPresent,true);assert.equal(f.authConfigured,true);assert.equal(f.databaseReadOptIn,true);assert.equal(f.ollamaModelPresent,true);
 assert.ok(!JSON.stringify(f).includes('private'));
});
test('startup probe connects without leaking secrets',async()=>{
 const logs=[];let closed=false;
 const result=await startupDatabaseCheck({DATABASE_URL:'postgres://private'},{createRepository:()=>({health:async()=>true,close:async()=>{closed=true;}}),log:(...x)=>logs.push(x.join(' '))});
 assert.equal(result,'connected');assert.equal(closed,true);assert.ok(!logs.join(' ').includes('private'));
});
test('failed database probe hides error detail',async()=>{
 const logs=[];const result=await startupDatabaseCheck({DATABASE_URL:'postgres://private'},{createRepository:()=>{throw Error('private');},log:(...x)=>logs.push(x.join(' '))});
 assert.equal(result,'failed');assert.ok(!logs.join(' ').includes('private'));
});

test('connection shape excludes secret material',()=>{const shape=connectionStringShape('postgresql://postgres:fictional@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres');assert.deepEqual(shape,{present:true,length:81,outerQuotes:false,postgresScheme:true,hasUserInfoAt:true,parsed:true,hostClass:'supabase_direct',port:'5432',usernamePresent:true,passwordPresent:true,databasePathPresent:true});});
