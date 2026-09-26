"""Create the public handoff from an explicit source allowlist; never include data."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
files = ['README.md', 'HANDOFF.md', 'CLAUDE-CODE-PROMPT.md', 'VALIDATION.md',
         'skincare.py', 'catalog.json', 'server.py', 'build_preview.py',
         'build_shopify.py', 'package_handoff.py', 'preview-api.js',
         'shopify-section-wrapper.liquid', 'netlify.toml', '.gitignore']
for folder in ['public', 'shopify', 'tests']:
    files.extend(str(p.relative_to(ROOT)) for p in (ROOT / folder).rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts)
destination = ROOT / 'preview-dist' / 'dermilogic-shopify-handoff.zip'
destination.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in sorted(files):
        archive.write(ROOT / name, 'dermilogic-skincare-quiz/' + name)
print(f'Packaged {len(files)} source, theme, and handoff files; no local data.')
