import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';

const port=18763,base='http://127.0.0.1:'+port;
const startServer=()=>spawn(process.execPath,['crm-server.mjs'],{
  env:{...process.env,PORT:String(port),CRM_BASIC_AUTH_USERNAME:'',CRM_BASIC_AUTH_PASSWORD:''},
  stdio:'pipe'
});
const waitForServer=async()=>{
  for(let i=0;i<50;i++){
    try{const r=await fetch(base+'/health');if(r.ok)return true}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  return false;
};

test('synthetic CRM browser journey',async()=>{
  const server=startServer();
  let browser;
  try{
    assert.equal(await waitForServer(),true,'server starts');
    const denied=await fetch(base+'/api/ai/analyze',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({leadId:'L-1001'})
    });
    assert.equal(denied.status,403,'fictional AI is disabled until configured');

    browser=await chromium.launch({headless:true});
    const page=await browser.newPage();
    await page.goto(base);

    await page.getByRole('button',{name:'Dashboard',exact:true}).click();
    assert.equal(await page.getByText('Sample leads').count(),1);

    await page.getByRole('button',{name:'Leads Inbox',exact:true}).click();
    assert.equal(await page.getByText('Aarav Rao').count()>0,true);

    await page.getByPlaceholder('Search leads, phone, location…').fill('Aarav');
    assert.equal(await page.getByRole('button',{name:/Aarav Rao/}).count(),1);
    await page.getByPlaceholder('Search leads, phone, location…').fill('');

    await page.getByRole('button',{name:/Aarav Rao/}).click();
    const headControls=page.locator('.headcontrols select');
    await headControls.nth(0).selectOption('Contacted');
    await headControls.nth(1).selectOption('Low');

    await page.getByRole('button',{name:'Requirements',exact:true}).click();
    await page.getByLabel('Preferred location').fill('Harlur Test');
    await page.getByLabel('Maximum monthly rent (₹)').fill('53000');
    await page.getByLabel('Operator notes').fill('Synthetic operator note');

    await page.reload();
    await page.getByRole('button',{name:'Leads Inbox',exact:true}).click();
    await page.getByRole('button',{name:/Aarav Rao/}).click();
    await page.getByRole('button',{name:'Requirements',exact:true}).click();
    assert.equal(await page.getByLabel('Preferred location').inputValue(),'Harlur Test');
    assert.equal(await page.getByLabel('Maximum monthly rent (₹)').inputValue(),'53000');
    assert.equal(await page.getByLabel('Operator notes').inputValue(),'Synthetic operator note');

    await page.getByRole('button',{name:'Overview',exact:true}).click();
    await page.getByLabel('When').fill('2026-10-15T10:00');
    await page.getByLabel('Note').fill('Fictional follow-up');
    await page.getByRole('button',{name:'Add follow-up'}).click();
    assert.equal(await page.getByText('Fictional follow-up').count(),1);
    await page.getByRole('button',{name:'Complete',exact:true}).click();
    assert.equal(await page.getByText('Completed').count()>0,true);

    await page.getByRole('button',{name:'Property Matches',exact:true}).click();
    await page.getByPlaceholder('Required audit reason').fill('Synthetic audit reason');
    await page.getByRole('button',{name:'Pin',exact:true}).first().click();
    assert.equal(await page.getByRole('button',{name:'Unpin',exact:true}).count()>0,true);
    await page.getByPlaceholder('Required audit reason').fill('Synthetic exclusion reason');
    await page.getByRole('button',{name:'Exclude',exact:true}).first().click();
    assert.equal(await page.getByRole('button',{name:'Undo exclude',exact:true}).count()>0,true);

    await page.getByRole('button',{name:'AI & Drafts',exact:true}).click();
    await page.getByRole('button',{name:'Run AI analysis',exact:true}).click();
    assert.equal(await page.getByText(/Ollama is disabled or unavailable/i).count()>0,true);

    const draft='Synthetic reply draft — not sent.';
    await page.locator('textarea').last().fill(draft);
    await page.reload();
    await page.getByRole('button',{name:'Leads Inbox',exact:true}).click();
    await page.getByRole('button',{name:/Aarav Rao/}).click();
    await page.getByRole('button',{name:'AI & Drafts',exact:true}).click();
    assert.equal(await page.locator('textarea').last().inputValue(),draft);

    await page.getByRole('button',{name:'Activity & History',exact:true}).click();
    assert.equal(await page.getByText(/Human edit: location/).count()>0,true);
    assert.equal(await page.getByText(/Scheduled follow-up/).count()>0,true);
    assert.equal(await page.getByText(/AI attempt: unavailable/).count()>0,true);

    await page.getByRole('button',{name:'Follow-ups',exact:true}).click();
    assert.equal(await page.getByText('Fictional follow-up').count(),1);

    await page.getByRole('button',{name:'Inventory',exact:true}).click();
    await page.getByPlaceholder('Search synthetic inventory…').fill('Whitefield');
    assert.equal(await page.getByText('3 BHK · Whitefield').count(),1);

    await page.getByRole('button',{name:'Settings',exact:true}).click();
    assert.equal(await page.getByText(/fictional fixtures only/i).count()>0,true);
  }finally{
    await browser?.close();
    server.kill();
  }
});
