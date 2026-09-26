import {timingSafeEqual} from 'node:crypto';
export function authorized(header,username,password){
 if(!username||!password)return false;
 if(typeof header!=='string'||header.length>8192||!header.startsWith('Basic '))return false;
 const token=header.slice(6);
 if(!/^[A-Za-z0-9+/]+={0,2}$/.test(token)||token.length%4!==0)return false;
 let decoded;try{decoded=Buffer.from(token,'base64').toString('utf8')}catch{return false}
 const expected=Buffer.from(username+':'+password),received=Buffer.from(decoded);
 return received.length===expected.length&&timingSafeEqual(received,expected);
}
export function accessMode(env){return Boolean(env.CRM_BASIC_AUTH_USERNAME)!==Boolean(env.CRM_BASIC_AUTH_PASSWORD)?'misconfigured':env.CRM_BASIC_AUTH_USERNAME?'protected':'synthetic-public';}
