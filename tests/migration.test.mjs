import test from 'node:test';
import assert from 'node:assert/strict';
import {migrationGuard,runMigration} from '../scripts/migrate-crm.mjs';

test('never migrates without explicit operator approval',()=>{
 assert.throws(()=>migrationGuard({DATABASE_URL:'fictional'}),/approval|APPROVED/);
 assert.throws(()=>migrationGuard({CRM_MIGRATION_APPROVED:'true'}),/DATABASE_URL/);
 assert.throws(()=>migrationGuard({CRM_MIGRATION_APPROVED:'true',DATABASE_URL:'fictional',CRM_REAL_DATA_ENABLED:'true'}),/Disable live/);
});

test('applies only pending migrations and closes connection',async()=>{
 const applied=new Set([1]);const calls=[];const db={
  query:async(sql,args)=>{
   calls.push([sql,args]);
   if(sql.startsWith('SELECT 1'))return{rows:applied.has(args[0])?[{x:1}]:[]};
   if(sql.startsWith('INSERT INTO crm_schema_migrations')){applied.add(args[0]);return{rows:[]}};
   return{rows:[]};
  },
  end:async()=>calls.push(['closed'])
 };
 const result=await runMigration({
  env:{CRM_MIGRATION_APPROVED:'true',DATABASE_URL:'fictional',CRM_REAL_DATA_ENABLED:'false'},
  dir:'/virtual',
  list:async()=>['001_first.sql','002_second.sql'],
  read:async(path)=>path.endsWith('001_first.sql')?'BEGIN; SELECT 1; COMMIT;':'BEGIN; SELECT 2; COMMIT;',
  connect:async()=>db
 });
 assert.deepEqual(result,{applied:true});
 assert.equal(calls.filter(x=>Array.isArray(x)&&x[0]==='BEGIN').length,0);
 assert.ok(calls.some(x=>typeof x[0]==='string'&&x[0].includes('SELECT 2')));
 assert.equal(calls.at(-1)[0],'closed');
});

test('rejects incomplete SQL before connecting',async()=>{
 await assert.rejects(runMigration({
  env:{CRM_MIGRATION_APPROVED:'true',DATABASE_URL:'fictional'},
  dir:'/virtual',
  list:async()=>['001_first.sql'],
  read:async()=> 'CREATE TABLE x(y int)',
  connect:async()=>{throw Error('should not connect')}
 }),/transaction/);
});
