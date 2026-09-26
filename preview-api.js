// Public review demo only: API behavior is simulated in this browser.
// No email addresses are transmitted to a server.
(() => {
 const originalFetch = window.fetch.bind(window);
 const storageKey = 'dermilogic-skincare-review-v2';
 const read = () => JSON.parse(localStorage.getItem(storageKey) || '{"leads":[],"events":{},"history":[]}');
 const write = data => localStorage.setItem(storageKey,JSON.stringify(data));
 const response = (data,status=200) => new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
 const recommend = answers => {
  const key=['concern','feel','sensitivity','routine','spf'].map(k=>answers?.[k]).join('|');
  const match=previewMatches[key];
  if(!match) throw Error('Please answer all five questions.');
  return match;
 };
 const event = (db,session,name) => { db.events[session] ||= {}; db.events[session][name]=true; };
 window.fetch = async (input,options={}) => {
  if(typeof input!=='string' || !input.startsWith('/api/')) return originalFetch(input,options);
  try {
   if(input==='/api/config') return response({csrf:'browser-preview',consent:previewConsent,preview:true});
   const body=options.body?JSON.parse(options.body):{};
   if(input==='/api/recommend') return response(recommend(body.answers));
   const db=read();
   if(input==='/api/events') {event(db,body.session,body.event);write(db);return response({ok:true});}
   if(input==='/api/leads' && options.method==='POST') {
    const email=String(body.email||'').trim().toLowerCase();
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||email.length>254||typeof body.marketing!=='boolean'||body.website) throw Error('Check your email and answers.');
    const match=recommend(body.answers), stamp=new Date().toISOString();
    const previous=db.leads.find(row=>row.email===email);
    const row={email,created_at:previous?.created_at||stamp,updated_at:stamp,answers:JSON.stringify(body.answers),head:match.key,marketing:Number(body.marketing),consent_text:previewConsent,consent_version:'browser-preview-v1',source:JSON.stringify(body.source||{}),session:body.session};
    db.leads=db.leads.filter(item=>item.email!==email);db.leads.unshift(row);
    db.history.push({email,marketing:row.marketing,recorded_at:stamp});event(db,body.session,'captured');write(db);
    return response({ok:true,delivery:'browser-only'});
   }
   if(input==='/api/leads') {
    const counts={};Object.values(db.events).forEach(events=>Object.keys(events).forEach(name=>counts[name]=(counts[name]||0)+1));
    return response({leads:db.leads,events:counts,opted:db.leads.filter(row=>row.marketing).length});
   }
   if(input==='/api/export') {
    const columns=['email','created_at','updated_at','head','marketing','consent_text','consent_version','source','answers'];
    const cell=value=>{let str=String(value??'');if(/^[\s]*[=+@-]/.test(str))str="'"+str;return '"'+str.replaceAll('"','""')+'"';};
    return new Response([columns.map(cell).join(','),...db.leads.map(row=>columns.map(key=>cell(row[key])).join(','))].join('\r\n'),{headers:{'Content-Type':'text/csv'}});
   }
   return response({error:'Unknown preview action.'},404);
  } catch(error) {
   return response({error:error.name==='QuotaExceededError'||error.name==='SecurityError'?'Browser storage is unavailable. You can still view your results without saving.':error.message},400);
  }
 };
})();
