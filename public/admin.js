const $ = id => document.getElementById(id);
let csrf, records=[];
async function load(){
 $('error').textContent='';
 try{
  const config=await fetch('/api/config'); if(!config.ok) throw Error('Cannot connect to the preview.');
  csrf=(await config.json()).csrf;
  const response=await fetch('/api/leads',{headers:{'X-CSRF-Token':csrf}});
  if(!response.ok) throw Error('Could not load leads. Try refreshing.');
  const data=await response.json(); records=data.leads;
  $('starts').textContent=data.events.started||0; $('completions').textContent=data.events.completed||0;
  $('leads').textContent=records.length; $('optins').textContent=data.opted;
  const rate=data.events.started?Math.round((data.events.captured||0)/data.events.started*100):0;
  $('funnel').textContent=`${rate}% of quiz attempts saved an email · ${data.events.shop_clicked||0} attempts clicked through to the shop`;
  render();
 }catch(e){$('error').textContent=e.message;}
}
function render(){
 const search=$('search').value.toLowerCase(), filter=$('filter').value;
 const rows=records.filter(r=>(r.email+' '+r.source).toLowerCase().includes(search)&&(filter==='all'||Boolean(r.marketing)===(filter==='yes')));
 $('rows').replaceChildren(); $('empty').hidden=rows.length>0;
 $('empty').textContent=records.length?'No leads match these filters.':'No leads yet. Complete the quiz with a test email to see your first record.';
 rows.forEach(r=>{
  const tr=document.createElement('tr'), source=JSON.parse(r.source), answers=JSON.parse(r.answers);
  [r.email,r.head[0].toUpperCase()+r.head.slice(1),answers.feel || 'Previous quiz',r.marketing?'Opted in':'Not opted in',[source.utm_source||'Direct',source.utm_campaign].filter(Boolean).join(' / '),new Date(r.updated_at).toLocaleString()].forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.append(td);});
  $('rows').append(tr);
 });
 $('count').textContent=`Showing ${rows.length} of ${records.length} saved emails`;
}
$('search').oninput=render; $('filter').onchange=render; $('refresh').onclick=load;
$('export').onclick=async()=>{
 $('export').disabled=true; $('error').textContent='';
 try{
  if(!csrf) throw Error('Refresh the dashboard before exporting.');
  const r=await fetch('/api/export',{headers:{'X-CSRF-Token':csrf}});
  if(!r.ok) throw Error('Could not export leads. Refresh and try again.');
  const url=URL.createObjectURL(await r.blob()),a=document.createElement('a');a.href=url;a.download='dermilogic-preview-leads.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }catch(e){$('error').textContent=e.message;}
 finally{$('export').disabled=false;}
};
load();
