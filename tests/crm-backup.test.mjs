import test from 'node:test';
import assert from 'node:assert/strict';
import {decodeBackupKey,encryptBackup,decryptBackup,assertBackupEnvironment,assertRestoreApproved} from '../src/crm-backup.mjs';

test('backup key must decode to exactly 32 bytes',()=>{
 const key=Buffer.alloc(32).toString('base64');
 assert.equal(decodeBackupKey(key)?.length,32);
 assert.equal(decodeBackupKey(Buffer.alloc(31).toString('base64')),null);
 assert.equal(decodeBackupKey('not-base64'),null);
});

test('backup envelope authenticates and decrypts',()=>{
 const key=Buffer.alloc(32,7),plain=Buffer.from('crm fictional backup payload');
 const envelope=encryptBackup(plain,key);
 assert.deepEqual(decryptBackup(envelope,key),plain);
 assert.throws(()=>decryptBackup(envelope,Buffer.alloc(32,8)),/authentication failed/);
});

test('backup environment requires CA and encryption key',()=>{
 const key=Buffer.alloc(32).toString('base64');
 assert.deepEqual(assertBackupEnvironment({DATABASE_URL:'db',DATABASE_SSL_CA:'ca',CRM_BACKUP_KEY:key}),Buffer.alloc(32));
 assert.throws(()=>assertBackupEnvironment({DATABASE_URL:'db',CRM_BACKUP_KEY:key}),/DATABASE_SSL_CA/);
});
test('restore always requires explicit approval',()=>assert.throws(()=>assertRestoreApproved({}),/CRM_RESTORE_APPROVED/));
