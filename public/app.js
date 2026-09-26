const $ = (id) => document.getElementById(id);
const questions = [
 {key:'concern',title:'What would you most like help with?',note:'Choose the concern that matters most to you today.',caption:'Your main concern',options:[['spots','Occasional spots & breakouts','I want a gentler way to care for blemish-prone skin.'],['dryness','Dryness or tightness','My skin often feels short on moisture.'],['tone','Uneven tone or lingering marks','I want to understand where to start.'],['simple','A simpler everyday routine','There are too many products and too much advice.'],['painful','Deep, painful, or persistent breakouts','I need help knowing the right next step.']]},
 {key:'feel',title:'How does your skin usually feel?',note:'This helps us suggest a starting texture, not diagnose your skin type.',caption:'Your everyday skin',options:[['dry','Mostly dry','Tight or dry-feeling through the day.'],['oily','Mostly oily','Shiny or oily-feeling through the day.'],['combination','A mix of both','Some areas feel oily, others dry.'],['balanced','Fairly comfortable','Neither especially dry nor oily.'],['unsure','I’m not sure','It changes, or I haven’t noticed a pattern.']]},
 {key:'sensitivity',title:'How does your skin respond to products?',note:'Comfort comes before adding another product.',caption:'Your skin’s comfort',options:[['comfortable','Usually comfortable','Most products I use feel fine.'],['reactive','Easily bothered','New products sometimes sting or irritate.'],['irritated','Irritated right now','Burning, raw, or persistently irritated.']]},
 {key:'routine',title:'What does your current routine look like?',note:'We’ll build on what you already do.',caption:'Your current routine',options:[['starting','I’m starting from scratch','I don’t have a consistent routine yet.'],['basic','I have a few basics','I already cleanse or moisturize regularly.'],['actives','I use treatment products','For example, exfoliating acids or retinol.'],['prescribed','I follow a prescribed plan','A healthcare professional guides my treatment.']]},
 {key:'spf',title:'Where does sunscreen fit in?',note:'Sun protection is part of the skincare foundation.',caption:'Your daily protection',options:[['daily','It’s a daily habit','I already use sunscreen regularly.'],['sometimes','Some days','I use it, but not consistently.'],['none','Not in my routine yet','I’d like to know what to look for.']]}
];
let step = 0, answers = {}, match, saved = false, csrf;
let advanceTimer, advancing = false, revision = 0, bundleRows = [];
let session = crypto.randomUUID();
const query = new URLSearchParams(location.search);
const source = Object.fromEntries(['utm_source','utm_medium','utm_campaign','utm_content'].filter(k=>query.has(k)).map(k=>[k,query.get(k).slice(0,160)]));
const config = fetch('/api/config').then(r=>{if(!r.ok) throw Error('Preview unavailable. Refresh and try again.'); return r.json();}).then(data=>{csrf=data.csrf; $('consent-copy').textContent=data.consent; return data;});
config.catch(()=>{});
async function api(path, data) {
 await config;
 const r = await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(data)});
 const body = await r.json();
 if(!r.ok) throw Error(body.error || 'Please try again.');
 return body;
}
function event(name){return api('/api/events',{event:name,session}).catch(()=>{});}
function show(id, focus){['intro','quiz','capture','results'].forEach(k=>$(k).hidden=k!==id); if(focus) $(focus).focus(); window.scrollTo({top:0,behavior:'instant'});}
function render(){
 clearTimeout(advanceTimer);
 const q=questions[step];
 $('step-label').textContent=`QUESTION ${step+1} OF ${questions.length}`; $('step-caption').textContent=q.caption;
 $('progress-fill').style.width=`${(step+1)/questions.length*100}%`; document.querySelector('.progress').setAttribute('aria-valuenow',step+1);
 $('question').textContent=q.title; $('question-note').textContent=q.note;
 $('options').replaceChildren();
 q.options.forEach(([value,title,detail])=>{
  const label=document.createElement('label'); label.className='option';
  const input=document.createElement('input'); input.type='radio'; input.name=q.key; input.value=value; input.checked=answers[q.key]===value;
  const words=document.createElement('span'), strong=document.createElement('strong'), small=document.createElement('small');
  strong.textContent=title; small.textContent=detail; words.append(strong,small); label.append(input,words); $('options').append(label);
  const choose=()=>{if(advancing)return;answers[q.key]=value;$('next').disabled=false;clearTimeout(advanceTimer);advanceTimer=setTimeout(advance,350);};
  input.addEventListener('change',choose);
  input.addEventListener('click',choose);
 });
 $('next').disabled=!answers[q.key]; $('next').textContent=step===questions.length-1?'Find my match →':'Continue →'; $('quiz-error').textContent='';
 show('quiz','question');
}
$('start').onclick=()=>{event('started'); render();};
$('back').onclick=()=>{clearTimeout(advanceTimer);revision++;advancing=false;if(step>0){step--;render();}else show('intro','start');};
async function advance(){
 clearTimeout(advanceTimer);
 if(advancing||!answers[questions[step].key])return;
 if(step<questions.length-1){step++;render();return;}
 advancing=true;const current=++revision;$('options').querySelectorAll('input').forEach(input=>input.disabled=true);
 $('next').disabled=true;$('next').textContent='Building your routine…';
 try{const result=await api('/api/recommend',{answers:{...answers}});if(current!==revision)return;match=result;event('completed');if(match.care) renderResults(); else show('capture','capture-title');}
 catch(err){if(current===revision)$('quiz-error').textContent=err.message;}
 finally{if(current===revision){advancing=false;$('options').querySelectorAll('input').forEach(input=>input.disabled=false);$('next').disabled=false;$('next').textContent='Try my results again →';}}
}
$('quiz-form').onsubmit=e=>{e.preventDefault();advance();};
$('edit').onclick=()=>{step=questions.length-1;render();};
$('lead-form').onsubmit=async e=>{
 e.preventDefault(); $('save').disabled=true; $('save').textContent='Saving…'; $('save-error').textContent='';
 try{await api('/api/leads',{email:$('email').value,marketing:$('marketing').checked,website:$('website').value,answers,source,session});saved=true;renderResults();}
 catch(err){$('save-error').textContent=err.message;}
 finally{$('save').disabled=false;$('save').textContent='Save my routine →';}
};
$('skip').onclick=()=>{saved=false;renderResults();};
function renderResults(){
 renderBundle();
 $('result-grid').hidden=!match.care;
 $('result-heading').textContent=match.title; $('match-why').textContent=match.why;
 $('match-name').textContent=match.care?'A professional can help you choose':match.name;
 $('product-label').textContent=match.care?'YOUR NEXT STEP':'WHERE DERMILOGIC CAN FIT';
 $('product-why').textContent=match.care?match.routine_note:match.product_why;
 $('result-image').src=`https://dermilogic.com/cdn/shop/files/${match.image}&width=800`; $('result-image').alt=match.name;
 $('result-image-wrap').hidden=match.care;
 $('result-grid').classList.toggle('care-result',match.care);
 $('routine-steps').replaceChildren();
 if(!match.care) match.steps.forEach(([title,copy],i)=>{const line=document.createElement('div');line.className='routine-line';const number=document.createElement('span');number.textContent=String(i+1).padStart(2,'0');const words=document.createElement('div');const strong=document.createElement('strong');strong.textContent=title;const p=document.createElement('p');p.textContent=copy;words.append(strong,p);line.append(number,words);$('routine-steps').append(line);});
 $('routine-note').textContent=match.routine_note;
 $('catalog-gap').textContent=match.care?'':match.gap;
 $('care-notice').textContent=match.notice;
 $('shop-link').href=match.shop; $('shop-link').textContent=match.shop_label+' ↗';
 $('saved-message').textContent=match.care?'Your next step is available without giving an email.':saved?'Saved in this local preview. No email has been sent.':'Your results are ready. No email was saved.';
 show('results','result-heading');
}
document.querySelectorAll('.shop-link').forEach(a=>a.addEventListener('click',()=>event('shop_clicked')));
$('restart').onclick=()=>{clearTimeout(advanceTimer);revision++;advancing=false;step=0;answers={};match=null;saved=false;session=crypto.randomUUID();$('lead-form').reset();$('save-error').textContent='';show('intro','start');};

function resolveBundleItem(item){return {...item};}
function bundleCurrency(){return 'USD';}
function money(cents){return new Intl.NumberFormat(undefined,{style:'currency',currency:bundleCurrency()}).format(cents/100);}
function renderBundle(){
 $('bundle').hidden=match.care;bundleRows=[];$('bundle-items').replaceChildren();$('bundle-message').textContent='';
 if(match.care)return;
 $('bundle-title').textContent=match.bundle_name;
 const seen=new Set();
 match.bundle.forEach(original=>{
  const item=resolveBundleItem(original);
  if(item.variant_id&&seen.has(item.variant_id))return;
  if(item.variant_id)seen.add(item.variant_id);
  const available=Boolean(item.available&&/^\d+$/.test(String(item.variant_id))&&Number.isFinite(item.price));
  const card=document.createElement('div');card.className='bundle-item';if(!item.image)card.classList.add('no-image');
  const pick=document.createElement('label');pick.className='bundle-pick';
  const input=document.createElement('input');input.type='checkbox';input.checked=available;input.disabled=!available;input.setAttribute('aria-label','Include '+item.title);
  const words=document.createElement('span'),title=document.createElement('strong'),variant=document.createElement('small');title.textContent=item.title;variant.textContent=item.variant_label||'1 item';words.append(title,variant);pick.append(input,words);
  const price=document.createElement('span');price.className='bundle-price';price.textContent=available?money(item.price):'Unavailable';
  const reason=document.createElement('p');reason.textContent=item.reason;
  if(item.image){const image=document.createElement('img');image.src=item.image;image.alt=item.title;image.width=120;image.height=120;image.loading='lazy';card.append(image);}
  card.append(pick,price,reason);
  if(item.url){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener';link.textContent='Product details ↗';link.className='bundle-details';card.append(link);}
  $('bundle-items').append(card);bundleRows.push({item,input,available});input.addEventListener('change',updateBundle);
 });
 updateBundle();
}
function selectedBundle(){return bundleRows.filter(row=>row.available&&row.input.checked).map(row=>row.item);}
function updateBundle(){
 const selected=selectedBundle();
 $('bundle-total').textContent=money(selected.reduce((sum,item)=>sum+item.price,0));
 $('bundle-count').textContent=`${selected.length} selected · 1 of each`;
 $('bundle-action').disabled=selected.length===0;
 $('bundle-action').textContent='Review selected items in store ↗';
 $('bundle-message').textContent=selected.length?'':'Choose at least one available item.';
}
$('bundle-action').onclick=async()=>{
 const items=selectedBundle();if(!items.length)return;
 event('shop_clicked');
 window.open('https://dermilogic.com/cart/'+items.map(item=>item.variant_id+':1').join(',')+'?storefront=true','_blank','noopener');
};
