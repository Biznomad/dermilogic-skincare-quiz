"""Browser checks use a temporary database, never the review database."""
import json
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from server import create_server

def run():
    output=ROOT/'test-results'; output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        db=Path(directory)/'browser.sqlite3'; server=create_server(db,0)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True)
                page=browser.new_page(viewport={'width':1440,'height':1000})
                errors=[]; page.on('pageerror',lambda e: errors.append(str(e)))
                page.goto(base+'/?utm_source=instagram&utm_campaign=reset-preview')
                page.locator('.hero-photo img').wait_for()
                
                for img in page.locator('#intro img').all(): expect(img).not_to_have_js_property('naturalWidth',0)
                page.screenshot(path=str(output/'desktop.png'),full_page=True)
                page.get_by_role('button',name='Find my routine').click()
                expect(page.locator('#next')).to_be_disabled()
                page.get_by_role('radio',name='Occasional spots',exact=False).check()
                page.locator('#next').click()
                page.locator('#back').click()
                expect(page.get_by_role('radio',name='Occasional spots',exact=False)).to_be_checked()
                page.locator('#next').click()
                page.get_by_role('radio',name='Mostly oily',exact=False).check(); page.locator('#next').click()
                page.get_by_role('radio',name='Usually comfortable',exact=False).check(); page.locator('#next').click()
                page.get_by_role('radio',name='I have a few basics',exact=False).check(); page.locator('#next').click()
                page.get_by_role('radio',name='Some days',exact=False).check(); page.locator('#next').click()
                expect(page.locator('#capture')).to_be_visible()
                expect(page.locator('#marketing')).not_to_be_checked()
                page.get_by_label('Your email address',exact=True).fill('shopper@example.com')
                page.route('**/api/leads',lambda route: route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'Test save failure. Try again.'})))
                page.locator('#save').click()
                expect(page.locator('#save-error')).to_contain_text('Test save failure')
                expect(page.locator('#capture')).to_be_visible()
                page.unroute('**/api/leads')
                page.locator('#marketing').check(); page.locator('#save').click()
                expect(page.locator('#results')).to_be_visible()
                expect(page.locator('#match-name')).to_have_text('Pimple Rescue Patches')
                expect(page.locator('#shop-link')).to_have_attribute('href','https://dermilogic.com/products/pimple-rescue-patch')
                expect(page.locator('#result-image')).not_to_have_js_property('naturalWidth',0)
                page.screenshot(path=str(output/'results.png'),full_page=True)
                page.goto(base+'/admin')
                expect(page.locator('#leads')).to_have_text('1'); expect(page.locator('#optins')).to_have_text('1')
                expect(page.locator('#rows')).to_contain_text('instagram / reset-preview')
                page.locator('#search').fill('nothing'); expect(page.locator('#empty')).to_be_visible()
                page.locator('#search').fill(''); page.locator('#filter').select_option('no'); expect(page.locator('#empty')).to_be_visible()
                page.locator('#filter').select_option('all')
                with page.expect_download() as download: page.locator('#export').click()
                assert 'shopper@example.com' in Path(download.value.path()).read_text()
                page.screenshot(path=str(output/'dashboard.png'),full_page=True)
                mobile=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
                mobile.on('pageerror',lambda e: errors.append(str(e)))
                mobile.goto(base)
                
                for img in mobile.locator('#intro img').all(): expect(img).not_to_have_js_property('naturalWidth',0)
                mobile.screenshot(path=str(output/'mobile.png'),full_page=True)
                assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
                mobile.locator('#start').click()
                for value in ['painful','oily','comfortable','basic','sometimes']:
                    mobile.locator(f'input[type=radio][value="{value}"]').check(); mobile.locator('#next').click()
                    assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
                expect(mobile.locator('#result-heading')).to_have_text('Get personal guidance first')
                expect(mobile.locator('#capture')).not_to_be_visible()
                expect(mobile.locator('#shop-link')).to_have_attribute('href','https://find-a-derm.aad.org/')
                expect(mobile.locator('#saved-message')).to_contain_text('without giving an email')
                mobile.screenshot(path=str(output/'mobile-results.png'),full_page=True)
                with sqlite3.connect(db) as connection:
                    assert connection.execute('SELECT COUNT(*) FROM leads').fetchone()[0]==1
                assert not errors,errors
                browser.close()
                print('PASS: desktop/mobile, real images, back navigation, unchecked consent, failed-save retry, capture, attribution, dashboard filters, CSV export, no-email path, no horizontal overflow, no JS errors.')
        finally:
            server.shutdown(); server.server_close(); thread.join()

if __name__=='__main__': run()
