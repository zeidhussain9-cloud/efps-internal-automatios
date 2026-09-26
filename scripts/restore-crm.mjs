import {spawn} from 'node:child_process';
import {mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {assertBackupEnvironment,assertRestoreApproved,decryptBackup} from '../src/crm-backup.mjs';
import {normalizeConnectionString} from '../src/crm-repository.mjs';

function connectionEnv(url,ca){const u=new URL(normalizeConnectionString(url));return{PATH:process.env.PATH||'',PGHOST:u.hostname,PGPORT:u.port||'5432',PGDATABASE:decodeURIComponent(u.pathname.slice(1)||'postgres'),PGUSER:decodeURIComponent(u.username),PGPASSWORD:u.password,PGSSLMODE:'verify-full',PGSSLROOTCERT:ca}}
function runRestore({url,ca,dumpFile}){return new Promise((resolvePromise,reject)=>{const child=spawn('pg_restore',['--exit-on-error','--no-owner','--no-privileges','--dbname','postgres',dumpFile],{env:connectionEnv(url,ca),stdio:['ignore','ignore','ignore']});child.on('error',reject);child.on('close',code=>code===0?resolvePromise():reject(Error('pg_restore failed')));})}

if(import.meta.url===new URL(process.argv[1],'file:').href){
 try{
  assertRestoreApproved(process.env);
  const key=assertBackupEnvironment(process.env);
  const input=resolve(process.env.CRM_BACKUP_INPUT||'');
  if(!input)throw Error('CRM_BACKUP_INPUT required');
  const payload=await readFile(input);
  const dump=decryptBackup(payload,key);
  const work=await mkdtemp(resolve(tmpdir(),'efps-crm-restore-'));
  const caPath=resolve(work,'ca.crt'),dumpPath=resolve(work,'dump.backup');
  await writeFile(caPath,process.env.DATABASE_SSL_CA,{mode:0o600});
  await writeFile(dumpPath,dump,{mode:0o600});
  try{await runRestore({url:process.env.DATABASE_URL,ca:caPath,dumpFile:dumpPath});console.log('CRM restore completed from authenticated backup.')}finally{await rm(work,{recursive:true,force:true})}
 }catch(e){console.error('CRM restore failed:',e.message);process.exitCode=1}
}