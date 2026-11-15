// Inventory's legacy readable timestamps are India-local, never host-local.
// New v5 records carry qualified ISO instants independently of display text.
export function inventoryInstant(value) {
 let raw=String(value??'').trim();
 if(!raw)return null;
 // Earlier CRM snapshots used a second explicit English display format.
 const short=raw.match(/^(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4}), (\d{1,2}):(\d{2}) (AM|PM)$/);
 if(short){
  const shortMonths=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const shortMonth=shortMonths.indexOf(short[2]);
  const calendar=new Date(Date.UTC(Number(short[3]),shortMonth,Number(short[1])));
  if(calendar.getUTCMonth()!==shortMonth||calendar.getUTCDate()!==Number(short[1]))return null;
  const fullMonths=['January','February','March','April','May','June','July','August','September','October','November','December'];
  const days=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  raw=`${days[calendar.getUTCDay()]}, ${fullMonths[shortMonth]} ${short[1]}, ${short[3]} at ${short[4]}:${short[5]}:00 ${short[6].toLowerCase()}`;
 }
 if(/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(raw)){
  const parsed=Date.parse(raw);return Number.isFinite(parsed)?parsed:null;
 }
 const m=raw.match(/^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday), (January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (\d{4}) at (\d{1,2}):(\d{2}):(\d{2}) (am|pm)$/i);
 if(!m)return null;
 const months=['january','february','march','april','may','june','july','august','september','october','november','december'];
 const weekdays=['sunday','monday','tuesday','wednesday','thursday','friday','saturday'];
 const month=months.indexOf(m[2].toLowerCase()),day=Number(m[3]),year=Number(m[4]),hour=Number(m[5]),minute=Number(m[6]),second=Number(m[7]);
 if(hour<1||hour>12||minute>59||second>59)return null;
 const calendar=new Date(Date.UTC(year,month,day));
 if(calendar.getUTCMonth()!==month||calendar.getUTCDate()!==day||weekdays[calendar.getUTCDay()]!==m[1].toLowerCase())return null;
 return Date.UTC(year,month,day,hour%12+(m[8].toLowerCase()==='pm'?12:0),minute,second)-330*60*1000;
}
