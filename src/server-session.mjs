import {randomBytes} from 'node:crypto';
import {authorized} from './server-auth.mjs';

const IDLE_MS=8*60*60*1000;
const MAX_MS=12*60*60*1000;
const COOKIE_NAME='efps_crm_session';
const COOKIE_MAX_AGE=Math.floor(MAX_MS/1000);
const sessions=new Map();
const failures=new Map();

const prune=()=>{const t=Date.now();for(const [token,s] of sessions){if(t-s.lastSeenAt>IDLE_MS||t-s.issuedAt>MAX_MS)sessions.delete(token)}for(const [key,v] of failures){if(t-v.startedAt>10*60*1000)failures.delete(key)}};
const clientKey=req=>String(req.headers['x-forwarded-for']||req.headers['x-real-ip']||'unknown').split(',')[0].trim();
const parseCookies=req=>{const out={};for(const part of String(req.headers.cookie||'').split(';')){const i=part.indexOf('=');if(i>0)out[part.slice(0,i).trim()]=decodeURIComponent(part.slice(i+1).trim())}return out};
const secureCookie=req=>String(req.headers['x-forwarded-proto']||'').split(',')[0].trim()==='https';

export function sameOrigin(req){
  const origin=req.headers.origin;if(!origin)return true;
  const proto=String(req.headers['x-forwarded-proto']||'http').split(',')[0].trim();
  const host=String(req.headers.host||'');
  try{return new URL(origin).origin===proto+'://'+host}catch{return false}
}
export function getRequestPrincipal(req,env){
  prune();
  const token=parseCookies(req)[COOKIE_NAME];
  const s=token?sessions.get(token):null;
  if(s){const t=Date.now();if(t-s.lastSeenAt<=IDLE_MS&&t-s.issuedAt<=MAX_MS){s.lastSeenAt=t;return{user:s.username,via:'session'}}sessions.delete(token)}
  if(authorized(String(req.headers.authorization||''),env.CRM_BASIC_AUTH_USERNAME,env.CRM_BASIC_AUTH_PASSWORD))return{user:env.CRM_BASIC_AUTH_USERNAME,via:'basic'};
  return null;
}
export function loginWithPassword(req,{username,password,env}){
  prune();const key=clientKey(req);const failed=failures.get(key);
  if(failed&&Date.now()-failed.startedAt<10*60*1000&&failed.count>=5)return{ok:false,status:429,error:'Too many sign-in attempts. Try again later.'};
  const basic=typeof username==='string'&&typeof password==='string'&&username&&password?'Basic '+Buffer.from(username+':'+password).toString('base64'):'';
  if(!authorized(basic,env.CRM_BASIC_AUTH_USERNAME,env.CRM_BASIC_AUTH_PASSWORD)){
    const v=failed&&Date.now()-failed.startedAt<10*60*1000?failed:{startedAt:Date.now(),count:0};v.count++;failures.set(key,v);
    return{ok:false,status:401,error:'Invalid operator credentials.'};
  }
  failures.delete(key);const token=randomBytes(32).toString('base64url');const t=Date.now();sessions.set(token,{username,issuedAt:t,lastSeenAt:t});
  return{ok:true,status:200,user:username,token};
}
export function revokeRequestSession(req){const token=parseCookies(req)[COOKIE_NAME];if(token)sessions.delete(token)}
export function sessionCookie(token,req){return COOKIE_NAME+'='+encodeURIComponent(token)+'; Path=/; HttpOnly; SameSite=Lax; Max-Age='+COOKIE_MAX_AGE+(secureCookie(req)?'; Secure':'')}
export function clearSessionCookie(req){return COOKIE_NAME+'=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT'+(secureCookie(req)?'; Secure':'')}
export function sessionPolicy(){return{idleMinutes:480,maxHours:12}}
