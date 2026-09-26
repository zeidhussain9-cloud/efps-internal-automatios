import test from 'node:test';import assert from 'node:assert/strict';import{STORAGE_KEY,readSynthetic,writeSynthetic,clearSynthetic}from '../src/synthetic-storage.mjs';
const memory=()=>{const map=new Map();return{getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v),removeItem:k=>map.delete(k)}};
test('synthetic state round trips with version',()=>{const s=memory(),v={leads:[{id:'Fictional'}],history:[],followups:[],drafts:{}};writeSynthetic(s,v);assert.deepEqual(readSynthetic(s).leads,v.leads);assert.equal(readSynthetic(s).version,1)});
test('corrupt and incompatible state fails closed',()=>{const s=memory();s.setItem(STORAGE_KEY,'{bad');assert.equal(readSynthetic(s),null);s.setItem(STORAGE_KEY,JSON.stringify({version:2,leads:[],history:[],followups:[]}));assert.equal(readSynthetic(s),null)});
test('reset removes stored synthetic state',()=>{const s=memory();writeSynthetic(s,{leads:[],history:[],followups:[]});clearSynthetic(s);assert.equal(readSynthetic(s),null)});
test('invalid state cannot be saved',()=>assert.throws(()=>writeSynthetic(memory(),{leads:[]})));
