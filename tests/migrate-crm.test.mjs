import test from 'node:test';
import assert from 'node:assert/strict';
import {migrationGuard,listMigrationFiles,runMigration} from '../scripts/migrate-crm.mjs';

test('migration guard requires explicit approval and keeps live ingestion disabled',()=>{
 assert.throws(()=>migrationGuard({DATABASE_URL:'db'}),/CRM_MIGRATION_APPROVED/);
 assert.throws(()=>migrationGuard({CRM_MIGRATION_APPROVED:'true'}),/DATABASE_URL/);
 assert.throws(()=>migrationGuard({CRM_MIGRATION_APPROVED:'true',DATABASE_URL:'db',CRM_REAL_DATA_ENABLED:'true'}),/Disable live data/);
 assert.doesNotThrow(()=>migrationGuard({CRM_MIGRATION_APPROVED:'true',DATABASE_URL:'db',CRM_REAL_DATA_ENABLED:'false'}));
});

test('migration files are numerically ordered',async()=>{
 const names=await listMigrationFiles({dir:'/virtual',list:async()=>['010_later.sql','002_second.sql','README.md','001_first.sql']});
 assert.deepEqual(names,['001_first.sql','002_second.sql','010_later.sql']);
});

test('runner applies only unapplied migrations in order',async()=>{
 const applied=new Set([1]),executed=[],queries=[];
 const db={
  query:async(sql,args)=>{
   queries.push([sql,args]);
   if(sql.startsWith('CREATE TABLE'))return{rows:[]};
   if(sql.startsWith('SELECT 1'))return{rows:applied.has(args[0])?[{x:1}]:[]};
   if(sql.startsWith('INSERT INTO crm_schema_migrations')){applied.add(args[0]);return{rows:[]}};
   executed.push(sql);return{rows:[]};
  },
  end:async()=>{}
 };
 const files={ '001_first.sql':'BEGIN; SELECT 1; COMMIT;','002_second.sql':'BEGIN; SELECT 2; COMMIT;'};
 const result=await runMigration({
  env:{CRM_MIGRATION_APPROVED:'true',DATABASE_URL:'postgresql://postgres:fictional@db.example.invalid:5432/postgres',CRM_REAL_DATA_ENABLED:'false'},
  dir:'/virtual',
  list:async()=>Object.keys(files),
  read:async(_p)=>files[_p.split('/').pop()],
  connect:async cfg=>{assert.equal(typeof cfg.connectionString,'string');assert.equal(cfg.sslCa,undefined);return db;}
 });
 assert.deepEqual(result,{applied:true});
 assert.equal(executed.length,1);assert.match(executed[0],/SELECT 2/);
 assert.ok(queries.some(q=>q[0].startsWith('INSERT INTO crm_schema_migrations')));
});
