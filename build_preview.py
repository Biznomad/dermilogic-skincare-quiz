"""Build a public UI demo. No database, credentials or server are published."""
import json
from pathlib import Path
from server import CONSENT
from skincare import OPTIONS, recommend
from itertools import product

ROOT = Path(__file__).resolve().parent
out = ROOT / 'preview-dist'
out.mkdir(exist_ok=True)
for name in ['index.html', 'admin.html', 'app.js', 'admin.js', 'style.css']:
    text = (ROOT / 'public' / name).read_text()
    if name.endswith('.html'):
        text = text.replace('<script src=', '<script src="/preview-api.js"></script><script src=', 1)
    for old, new in [
        ('LOCAL PREVIEW', 'REVIEW PREVIEW'),
        ('Use a test email. Nothing is sent.', 'Test emails only. Saved in this browser.'),
        ('Test records only. No email integration connected.', 'Test records in this browser only. Nothing is sent.'),
        ('Preview only: saves to this computer.', 'Preview only: saves in this browser.'),
        ('Saved in this local preview.', 'Saved in this browser for review.'),
        ('Local review dashboard', 'Browser-only review dashboard'),
        ('Local preview', 'Review preview')
    ]:
        text = text.replace(old, new)
    (out / name).write_text(text)
shim = (ROOT / 'preview-api.js').read_text()
# Intern repeated content so the same reviewed rules also ship efficiently to Shopify.
values=[]; value_ids={}; rows={}
for answer_values in product(*(sorted(v) for v in OPTIONS.values())):
    result=recommend(dict(zip(OPTIONS,answer_values)))
    fields=list(result)
    ids=[]
    for value in result.values():
        encoded=json.dumps(value,sort_keys=True)
        if encoded not in value_ids:
            value_ids[encoded]=len(values); values.append(value)
        ids.append(value_ids[encoded])
    rows['|'.join(answer_values)]=ids
engine='window.DermilogicMatches = (() => { const fields='+json.dumps(fields)+'; const values='+json.dumps(values)+'; const rows='+json.dumps(rows)+"; return Object.fromEntries(Object.entries(rows).map(([key,ids])=>[key,Object.fromEntries(fields.map((field,i)=>[field,values[ids[i]]]))])); })();\n"
(ROOT / 'generated-matches.js').write_text(engine)
(out / 'preview-api.js').write_text(engine+'const previewMatches = window.DermilogicMatches;\nconst previewConsent = ' + json.dumps(CONSENT) + ';\n' + shim)
(out / '_redirects').write_text('/admin /admin.html 200\n')
(out / '_headers').write_text('''/*
  X-Robots-Tag: noindex, nofollow
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
  Content-Security-Policy: default-src 'self'; img-src 'self' https://dermilogic.com; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'
''')
print('Built browser-only review preview: 8 public files; no customer database.')
