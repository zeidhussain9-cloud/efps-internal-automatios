import {readCanonicalInventory,syncInventorySnapshot} from '../src/inventory-sync.mjs';
try{
 const rows=await readCanonicalInventory(process.env);
 const result=await syncInventorySnapshot({rows});
 console.log(JSON.stringify({ok:true,...result}));
}catch(error){
 console.error('Inventory sync failed:',error?.message||String(error));
 process.exitCode=1;
}
