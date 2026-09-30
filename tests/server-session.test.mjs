import test from 'node:test';import assert from 'node:assert/strict';import{sessionPolicy,sameOrigin}from '../src/server-session.mjs';
test('session policy has bounded lifetime',()=>{assert.deepEqual(sessionPolicy(),{idleMinutes:480,maxHours:12})});
test('same-origin accepts same host and rejects foreign origin',()=>{assert.equal(sameOrigin({headers:{origin:'http://127.0.0.1:2000',host:'127.0.0.1:2000'}}),true);assert.equal(sameOrigin({headers:{origin:'https://evil.example',host:'127.0.0.1:2000'}}),false);assert.equal(sameOrigin({headers:{host:'127.0.0.1:2000'}}),true)});
