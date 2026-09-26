"""Generate installable Shopify assets from the reviewed quiz source."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
out=ROOT/'shopify'
html=(ROOT/'public/index.html').read_text()
main=html[html.index('<main'):html.index('</main>')+7]
start=main.index('<section id="capture"');end=main.index('<section id="results"')
main=main[:start]+main[end:]
main=main.replace('Your skin.<br>A clearer <em>direction.</em>', '{{ section.settings.heading | escape }}').replace('Breakouts, dry-feeling skin, or simply too much advice? Tell us what’s on your mind. Leave with a practical routine and products that have a reason to be there.', '{{ section.settings.intro | escape }}')
main=main.replace('Find my routine <span', '{{ section.settings.button_label | escape }} <span')
main=main.replace('<div class="hero-photo"><img src="https://dermilogic.com/cdn/shop/files/dl-cleanser-sink.jpg?v=1789177321&width=1200" alt="The Reset Cleanser beside a folded towel">', '<div class="hero-photo">{% if section.settings.hero_image != blank %}{{ section.settings.hero_image | image_url: width: 1200 | image_tag: loading: "lazy", alt: section.settings.hero_image.alt }}{% else %}<div class="image-placeholder">Your skin.<br>Your starting point.</div>{% endif %}')
# No cross-store or fixed promotional images in an installable theme section.
import re
main=re.sub(r'<img src="https://dermilogic.com[^"]*"[^>]*>', '',main)
css=(ROOT/'public/style.css').read_text().replace(':root', ':host').replace('body{', ':host{')
css+='\n.image-placeholder{padding:70px 35px;font:40px/1.2 var(--display)}:host{display:block}\n'
(out/'assets/dermilogic-skin-quiz.css').write_text(css)
app=(ROOT/'public/app.js').read_text()
app=app.replace('const $ = (id) => document.getElementById(id);','const root = this.attachShadow({mode:"open"}); root.append(this.querySelector("template").content.cloneNode(true)); const existingSignup=this.querySelector("[data-newsletter]"); if(existingSignup?.querySelector("[data-form-result]"))existingSignup.hidden=false; const $ = id => root.getElementById(id); const host=this;')
start=app.index('const query =');end=app.index('function event(name)',start)
app=app[:start]+"""async function api(path,data){
 const key=['concern','feel','sensitivity','routine','spf'].map(k=>data.answers?.[k]).join('|');
 const result=window.DermilogicMatches[key];
 if(!result) throw Error('Please complete all five questions.');
 return structuredClone(result);
}
"""+app[end:]
start=app.index('function event(name)');end=app.index('function show(',start)
app=app[:start]+"function event(){}\n"+app[end:]
app=app.replace("['intro','quiz','capture','results']","['intro','quiz','results']").replace("document.querySelector('.progress')","root.querySelector('.progress')").replace("document.createElement", "document.createElement")
app=app.replace("window.scrollTo({top:0,behavior:'instant'});","host.scrollIntoView({block:'start',behavior:'instant'});")
app=app.replace("if(match.care) renderResults(); else show('capture','capture-title');", "renderResults();")
start=app.index("$('edit').onclick");end=app.index('function renderResults()',start)
app=app[:start]+app[end:]
app=app.replace("function renderResults(){", """function renderResults(){
 const signup=host.querySelector('[data-newsletter]');if(signup)signup.hidden=match.care;
 if(!match.care){
  const kind=match.name==='Pimple Rescue Patches'?'patches':'cleanser';
  const product=host.querySelector('[data-product="'+kind+'"]');
  match.available=product?.dataset.available==='true';
  match.shop=product?.dataset.url||'';
  match.name=product?.dataset.title||'A suitable '+(kind==='patches'?'hydrocolloid patch':'gentle cleanser');
  match.product_why=product?.dataset.description||match.product_why;
  match.shop_label='Explore '+match.name;
  match.fullImage=product?.dataset.image||'';
 }
""")
app=app.replace("$('result-image').src=`https://dermilogic.com/cdn/shop/files/${match.image}&width=800`;", "$('result-image').src=match.fullImage||'';")
app=app.replace("$('result-image-wrap').hidden=match.care;", "$('result-image-wrap').hidden=match.care||!match.fullImage;")
app=app.replace("$('shop-link').href=match.shop;", "$('shop-link').hidden=!match.care&&!match.available; $('shop-link').href=match.shop||'#';")
app=app.replace("saved?'Saved in this local preview. No email has been sent.':'Your results are ready. No email was saved.'", "'Your results are ready. No email needed.'")
start=app.index("document.querySelectorAll('.shop-link')")
app=app[:start]+"""$('restart').onclick=()=>{step=0;answers={};match=null;saved=false;const signup=host.querySelector('[data-newsletter]');if(signup)signup.hidden=true;show('intro','start');};
"""
engine=(ROOT/'generated-matches.js').read_text()
runtime=engine+"\nif(!customElements.get('dermilogic-skin-quiz'))customElements.define('dermilogic-skin-quiz',class extends HTMLElement { connectedCallback(){if(this.shadowRoot)return;\n"+app+"\n}});\n"
(out/'assets/dermilogic-skin-quiz.js').write_text(runtime)
wrapper=(ROOT/'shopify-section-wrapper.liquid').read_text()
(out/'sections/dermilogic-skin-quiz.liquid').write_text(wrapper.replace('<!-- QUIZ_CONTENT -->',main))
(out/'templates/page.skin-quiz.json').write_text(json.dumps({'sections':{'main':{'type':'dermilogic-skin-quiz','settings':{}}},'order':['main']},indent=2))
print('Generated Shopify section, JS/CSS assets and page template.')
