import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
const port=18763,base='http://127.0.0.1:'+port;
test('synthetic CRM browser journey',async t=>{
 const server=spawn(process.execPath,['crm-server.mjs'],{env:{...process.env,PORT:String(port),CRM_BASIC_AUTH_USERNAME:'',CRM_BASIC_AUTH_PASSWORD:''},stdio:'pipe'});
 let browser;
 try{
  let ready=false;for(let i=0;i<50;i++){try{const r=await fetch(base+'/health');if(r.ok){ready=true;break}}catch{}await new Promise(resolve=>setTimeout(resolve,200))}
  assert.equal(ready,true,'server starts');
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage();
  await page.goto(base);
  await page.getByRole('button',{name:'Leads Inbox'}).click();
  await page.getByRole('button',{name:/Aarav Rao/}).click();
  await page.getByRole('button',{name:'Requirements'}).click();
  await page.getByLabel('Preferred location').fill('Harlur Test');
  await page.reload();
  await page.getByRole('button',{name:'Leads Inbox'}).click();
  await page.getByRole('button',{name:/Aarav Rao/}).click();
  await page.getByRole('button',{name:'Requirements'}).click();
  assert.equal(await page.getByLabel('Preferred location').inputValue(),'Harlur Test');
  await page.getByRole('button',{name:'Overview'}).click();
  await page.getByLabel('When').fill('2026-10-15T10:00');
  await page.getByLabel('Note').fill('Fictional follow-up');
  await page.getByRole('button',{name:'Add follow-up'}).click();
  await page.getByRole('button',{name:'Follow-ups'}).click();
  assert.equal(await page.getByText('Fictional follow-up').count(),1);
  await page.getByRole('button',{name:'Inventory'}).click();
  await page.getByPlaceholder('Search synthetic inventory…').fill('Whitefield');
  assert.equal(await page.getByText('3 BHK · Whitefield').count(),1);
  await page.getByRole('button',{name:'Settings'}).click();
  assert.equal(await page.getByText(/fictional records only/i).count()>0,true);
 }finally{await browser?.close();server.kill();}
});
