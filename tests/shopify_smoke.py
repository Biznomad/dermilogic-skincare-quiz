"""Browser test for packaged assets; Shopify Liquid is separately validated."""
import functools
import re
import tempfile
import threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]

def run():
 with tempfile.TemporaryDirectory() as directory:
  tmp=Path(directory)
  for source in (ROOT/'shopify/assets').iterdir(): (tmp/source.name).write_bytes(source.read_bytes())
  liquid=(ROOT/'shopify/sections/dermilogic-skin-quiz.liquid').read_text()
  template=liquid.split('<template>')[1].split('</template>')[0]
  template=template.replace("{{ 'dermilogic-skin-quiz.css' | asset_url }}",'/dermilogic-skin-quiz.css')
  template=re.sub(r'{{.*?}}|{%.*?%}','',template,flags=re.S)
  html='<html><body><h1 id="outside">Theme heading</h1><dermilogic-skin-quiz><template>'+template+'</template><div hidden data-product="cleanser" data-title="Fixture Cleanser" data-url="/products/cleanser" data-available="true" data-description="Fixture explanation"></div><div hidden data-product="patches" data-title="Fixture Patches" data-url="/products/patches" data-available="true"></div><div data-newsletter hidden><form><label>Email<input type="email" name="contact[email]" required></label><label><input type="checkbox" name="contact[accepts_marketing]" required>I agree</label><button>Join</button></form></div></dermilogic-skin-quiz><script src="/dermilogic-skin-quiz.js" defer></script></body></html>'
  (tmp/'index.html').write_text(html)
  class Quiet(SimpleHTTPRequestHandler):
   def log_message(self,*args): pass
  server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=directory))
  thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with sync_playwright() as p:
    browser=p.webkit.launch()
    page=browser.new_page(**p.devices['iPad (gen 7)'])
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(f'http://127.0.0.1:{server.server_port}')
    expect(page.locator('#outside')).to_have_css('font-family','-webkit-standard')
    page.locator('#start').click()
    for value in ['dryness','dry','reactive','starting','none']:
     page.locator(f'input[type=radio][value="{value}"]').check();page.locator('#next').click()
    expect(page.locator('#result-heading')).to_have_text('Keep your routine gentle')
    expect(page.locator('#match-name')).to_have_text('Fixture Cleanser')
    expect(page.locator('[data-newsletter]')).to_be_visible()
    expect(page.locator('[name="contact[accepts_marketing]"]')).not_to_be_checked()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert page.evaluate('localStorage.length')==0
    page.locator('#restart').click()
    expect(page.locator('[data-newsletter]')).not_to_be_visible()
    page.locator('#start').click()
    for value in ['painful','oily','comfortable','basic','daily']:
     page.locator(f'input[type=radio][value="{value}"]').check();page.locator('#next').click()
    expect(page.locator('#shop-link')).to_have_attribute('href','https://find-a-derm.aad.org/')
    expect(page.locator('[data-newsletter]')).not_to_be_visible()
    page.locator('#restart').click()
    page.evaluate("document.querySelector('[data-product=cleanser]').dataset.available='false'")
    page.locator('#start').click()
    for value in ['simple','balanced','comfortable','basic','daily']:
     page.locator(f'input[type=radio][value="{value}"]').check();page.locator('#next').click()
    expect(page.locator('#shop-link')).not_to_be_visible()
    page.evaluate("const old=document.querySelector('dermilogic-skin-quiz');const fresh=old.cloneNode(true);old.replaceWith(fresh)")
    page.locator('#start').click();expect(page.locator('#question')).to_contain_text('most like help')
    assert not errors,errors
    browser.close()
    print('PASS: packaged Shopify assets in iPad WebKit; isolated CSS, concern routing, product overrides, optional consent, no saved skin data, professional guidance, unavailable products, theme-editor-style reinsertion.')
  finally:
   server.shutdown();server.server_close();thread.join()
if __name__=='__main__':run()
