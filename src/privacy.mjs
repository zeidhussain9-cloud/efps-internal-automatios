export function maskPhone(phone){
  const value=String(phone||'');const digits=value.replace(/\D/g,'');if(!digits)return '';
  return (value.trim().startsWith('+91')?'+91 ':'')+'******'+digits.slice(-4);
}
export function maskMessage(){return'[Sensitive message hidden — reveal sensitive data to view]';}
