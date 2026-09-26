const $ = (id) => document.getElementById(id);
const questions = [
 {key:'concern',title:'What would you most like help with?',note:'Choose the concern that matters most to you today.',caption:'Your main concern',options:[['spots','Occasional spots & breakouts','I want a gentler way to care for blemish-prone skin.'],['dryness','Dryness or tightness','My skin often feels short on moisture.'],['tone','Uneven tone or lingering marks','I want to understand where to start.'],['simple','A simpler everyday routine','There are too many products and too much advice.'],['painful','Deep, painful, or persistent breakouts','I need help knowing the right next step.']]},
 {key:'feel',title:'How does your skin usually feel?',note:'This helps us suggest a starting texture, not diagnose your skin type.',caption:'Your everyday skin',options:[['dry','Mostly dry','Tight or dry-feeling through the day.'],['oily','Mostly oily','Shiny or oily-feeling through the day.'],['combination','A mix of both','Some areas feel oily, others dry.'],['balanced','Fairly comfortable','Neither especially dry nor oily.'],['unsure','I’m not sure','It changes, or I haven’t noticed a pattern.']]},
 {key:'sensitivity',title:'How does your skin respond to products?',note:'Comfort comes before adding another product.',caption:'Your skin’s comfort',options:[['comfortable','Usually comfortable','Most products I use feel fine.'],['reactive','Easily bothered','New products sometimes sting or irritate.'],['irritated','Irritated right now','Burning, raw, or persistently irritated.']]},
 {key:'routine',title:'What does your current routine look like?',note:'We’ll build on what you already do.',caption:'Your current routine',options:[['starting','I’m starting from scratch','I don’t have a consistent routine yet.'],['basic','I have a few basics','I already cleanse or moisturize regularly.'],['actives','I use treatment products','For example, exfoliating acids or retinol.'],['prescribed','I follow a prescribed plan','A healthcare professional guides my treatment.']]},
 {key:'spf',title:'Where does sunscreen fit in?',note:'Sun protection is part of the skincare foundation.',caption:'Your daily protection',options:[['daily','It’s a daily habit','I already use sunscreen regularly.'],['sometimes','Some days','I use it, but not consistently.'],['none','Not in my routine yet','I’d like to know what to look for.']]}
];
let step = 0, answers = {}, match, saved = false, csrf;
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
  input.addEventListener('change',()=>{answers[q.key]=value; $('next').disabled=false;});
 });
 $('next').disabled=!answers[q.key]; $('next').textContent=step===questions.length-1?'Find my match →':'Continue →'; $('quiz-error').textContent='';
 show('quiz','question');
}
$('start').onclick=()=>{event('started'); render();};
$('back').onclick=()=>{if(step>0){step--;render();}else show('intro','start');};
$('quiz-form').onsubmit=async e=>{
 e.preventDefault(); if(!answers[questions[step].key]) return;
 if(step<questions.length-1){step++;render();return;}
 $('next').disabled=true; $('next').textContent='Finding your match…';
 try{match=await api('/api/recommend',{answers});event('completed');if(match.care) renderResults(); else show('capture','capture-title');}
 catch(err){$('quiz-error').textContent=err.message;}
 finally{$('next').disabled=false;$('next').textContent='Find my match →';}
};
$('edit').onclick=()=>{step=questions.length-1;render();};
$('lead-form').onsubmit=async e=>{
 e.preventDefault(); $('save').disabled=true; $('save').textContent='Saving…'; $('save-error').textContent='';
 try{await api('/api/leads',{email:$('email').value,marketing:$('marketing').checked,website:$('website').value,answers,source,session});saved=true;renderResults();}
 catch(err){$('save-error').textContent=err.message;}
 finally{$('save').disabled=false;$('save').textContent='Save my routine →';}
};
$('skip').onclick=()=>{saved=false;renderResults();};
function renderResults(){
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
$('restart').onclick=()=>{step=0;answers={};match=null;saved=false;session=crypto.randomUUID();$('lead-form').reset();$('save-error').textContent='';show('intro','start');};
