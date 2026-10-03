import test from 'node:test';
import assert from 'node:assert/strict';
import {
  sessionPolicy,
  sameOrigin,
  loginWithPassword,
  resetAuthStateForTests,
  LOGIN_FAILURE_LIMIT,
  LOGIN_FAILURE_WINDOW_MS,
} from '../src/server-session.mjs';

test('session policy has bounded lifetime',()=>{
  assert.deepEqual(sessionPolicy(),{idleMinutes:480,maxHours:12});
});

test('same-origin accepts same host and rejects foreign origin',()=>{
  assert.equal(sameOrigin({headers:{origin:'http://127.0.0.1:2000',host:'127.0.0.1:2000'}}),true);
  assert.equal(sameOrigin({headers:{origin:'https://evil.example',host:'127.0.0.1:2000'}}),false);
  assert.equal(sameOrigin({headers:{host:'127.0.0.1:2000'}}),true);
});

test('login rate-limit constants are conservative',()=>{
  assert.equal(LOGIN_FAILURE_LIMIT,5);
  assert.equal(LOGIN_FAILURE_WINDOW_MS,10*60*1000);
});

test('failed logins increment and lock out after limit',()=>{
  resetAuthStateForTests();
  const env={CRM_BASIC_AUTH_USERNAME:'operator',CRM_BASIC_AUTH_PASSWORD:'correct-horse'};
  const req={headers:{'x-forwarded-for':'203.0.113.10'}};

  for(let i=0;i<LOGIN_FAILURE_LIMIT;i++){
    const result=loginWithPassword(req,{username:'operator',password:'wrong',env});
    assert.equal(result.ok,false);
    assert.equal(result.status,401);
  }

  const locked=loginWithPassword(req,{username:'operator',password:'wrong',env});
  assert.equal(locked.ok,false);
  assert.equal(locked.status,429);
  assert.match(String(locked.error),/Too many sign-in attempts/i);

  // Even the correct password is rejected while locked out.
  const stillLocked=loginWithPassword(req,{username:'operator',password:'correct-horse',env});
  assert.equal(stillLocked.ok,false);
  assert.equal(stillLocked.status,429);
});

test('successful login clears failure counter for that client',()=>{
  resetAuthStateForTests();
  const env={CRM_BASIC_AUTH_USERNAME:'operator',CRM_BASIC_AUTH_PASSWORD:'correct-horse'};
  const req={headers:{'x-forwarded-for':'203.0.113.20'}};

  for(let i=0;i<LOGIN_FAILURE_LIMIT-1;i++){
    const result=loginWithPassword(req,{username:'operator',password:'wrong',env});
    assert.equal(result.status,401);
  }

  const ok=loginWithPassword(req,{username:'operator',password:'correct-horse',env});
  assert.equal(ok.ok,true);
  assert.equal(ok.status,200);
  assert.ok(ok.token);

  // After success, failures are cleared — another wrong attempt is 401, not 429.
  const after=loginWithPassword(req,{username:'operator',password:'wrong',env});
  assert.equal(after.ok,false);
  assert.equal(after.status,401);
});

test('rate-limit counters are isolated per client key',()=>{
  resetAuthStateForTests();
  const env={CRM_BASIC_AUTH_USERNAME:'operator',CRM_BASIC_AUTH_PASSWORD:'correct-horse'};
  const clientA={headers:{'x-forwarded-for':'198.51.100.1'}};
  const clientB={headers:{'x-forwarded-for':'198.51.100.2'}};

  for(let i=0;i<LOGIN_FAILURE_LIMIT;i++){
    assert.equal(loginWithPassword(clientA,{username:'operator',password:'wrong',env}).status,401);
  }
  assert.equal(loginWithPassword(clientA,{username:'operator',password:'wrong',env}).status,429);

  // Different client is not locked.
  const other=loginWithPassword(clientB,{username:'operator',password:'correct-horse',env});
  assert.equal(other.ok,true);
  assert.equal(other.status,200);
});
