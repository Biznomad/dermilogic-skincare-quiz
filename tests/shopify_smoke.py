"""Browser test for packaged assets; Shopify Liquid is separately validated."""
import functools
import json
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
  fixtures=''.join(f'<div hidden data-product="{kind}" data-title="Fixture {kind}" data-url="/products/{kind}" data-available="true" data-variant-id="{variant}" data-price="{price}" data-variant-label="Default"></div>' for kind,variant,price in [('cleanser',101,1500),('patches',102,1000),('towels',103,1200),('bands',104,900)])
  html='<html><body><h1 id="outside">Theme heading</h1><dermilogic-skin-quiz data-currency="USD" data-root="/fr/" data-cart-url="/fr/cart"><template>'+template+'</template>'+fixtures+'<div data-newsletter hidden><form><label>Email<input type="email" name="contact[email]" required></label><label><input type="checkbox" name="contact[accepts_marketing]" required>I agree</label><button>Join</button></form></div></dermilogic-skin-quiz><script src="/dermilogic-skin-quiz.js" defer></script></body></html>'

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
    def answer(value):
     field=page.locator(f'input[type=radio][value="{value}"]')
     field.check();expect(field).not_to_be_visible()
    page.locator('#start').click()
    answer('dryness')
    page.locator('#back').click()
    expect(page.locator('input[value="dryness"]')).to_be_checked()
    page.locator('input[value="dryness"]').click()
    expect(page.locator('input[value="dryness"]')).not_to_be_visible()
    for value in ['dry','reactive','starting','none']:answer(value)
    expect(page.locator('#result-heading')).to_have_text('Keep your routine gentle')
    expect(page.locator('#bundle-title')).to_have_text('Your gentle-care bundle')
    expect(page.locator('.bundle-item')).to_have_count(2)
    expect(page.locator('#bundle-total')).to_have_text('$27.00')
    expect(page.locator('[data-newsletter]')).to_be_visible()
    expect(page.locator('[name="contact[accepts_marketing]"]')).not_to_be_checked()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert page.evaluate('localStorage.length')==0
    page.get_by_role('checkbox',name='Include Fixture towels',exact=True).uncheck()
    expect(page.locator('#bundle-total')).to_have_text('$15.00')
    requests=[]
    def failed_cart(route):
     requests.append(route.request.post_data_json)
     route.fulfill(status=422,content_type='application/json',body=json.dumps({'description':'Fixture stock changed. Check your cart.'}))
    page.route('**/fr/cart/add.js',failed_cart)
    page.locator('#bundle-action').click()
    expect(page.locator('#bundle-message')).to_contain_text('Fixture stock changed')
    expect(page.locator('#bundle-action')).to_be_enabled()
    assert requests==[{'items':[{'id':'101','quantity':1}]}],requests
    page.unroute('**/fr/cart/add.js')
    page.route('**/fr/cart/add.js',lambda route:route.fulfill(status=200,content_type='application/json',body='{"items":[]}'))
    page.route('**/fr/cart',lambda route:route.fulfill(status=200,content_type='text/html',body='<h1>Fixture cart</h1>'))
    page.locator('#bundle-action').click()
    expect(page.get_by_role('heading',name='Fixture cart')).to_be_visible()
    page.goto(f'http://127.0.0.1:{server.server_port}')
    page.locator('#start').click()
    for value in ['painful','oily','comfortable','basic','daily']:answer(value)
    expect(page.locator('#shop-link')).to_have_attribute('href','https://find-a-derm.aad.org/')
    expect(page.locator('#bundle')).not_to_be_visible()
    expect(page.locator('[data-newsletter]')).not_to_be_visible()
    page.locator('#restart').click()
    page.evaluate("document.querySelector('[data-product=cleanser]').dataset.available='false'; document.querySelector('[data-product=bands]').dataset.available='false'")
    page.locator('#start').click()
    for value in ['simple','balanced','comfortable','starting','daily']:answer(value)
    expect(page.locator('#bundle-action')).to_be_disabled()
    expect(page.locator('#bundle-total')).to_have_text('$0.00')
    page.locator('#restart').click()
    page.evaluate("document.querySelector('[data-product=cleanser]').dataset.available='true'; document.querySelector('[data-product=bands]').dataset.available='true'; document.querySelector('[data-product=bands]').dataset.variantId='101'")
    page.locator('#start').click()
    for value in ['simple','balanced','comfortable','starting','daily']:answer(value)
    expect(page.locator('.bundle-item')).to_have_count(1)
    expect(page.locator('#bundle-total')).to_have_text('$15.00')
    page.evaluate("const old=document.querySelector('dermilogic-skin-quiz');const fresh=old.cloneNode(true);old.replaceWith(fresh)")
    page.locator('#start').click();expect(page.locator('#question')).to_contain_text('most like help')
    assert not errors,errors
    browser.close()
    print('PASS: Shopify iPad auto-progress/back/reselection; dynamic bundles, removal/totals, unavailable and duplicate variants, localized cart payload/error/success, no skin data, care paths, section reinsertion.')
  finally:
   server.shutdown();server.server_close();thread.join()
if __name__=='__main__':run()
