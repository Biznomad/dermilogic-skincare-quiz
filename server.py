"""Local review server. No email delivery or external account access."""
import argparse
import csv
import io
import json
import re
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
from skincare import OPTIONS, recommend
CONSENT = 'Yes, send me Dermilogic product news and offers by email. I can unsubscribe at any time.'

def now():
    return datetime.now(timezone.utc).isoformat()

def create_server(db_path, port=8891):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS leads (
          email TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          answers TEXT NOT NULL, head TEXT NOT NULL, marketing INTEGER NOT NULL,
          consent_text TEXT NOT NULL, consent_version TEXT NOT NULL, source TEXT NOT NULL,
          session TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS consent_history (
          id INTEGER PRIMARY KEY, email TEXT NOT NULL, recorded_at TEXT NOT NULL,
          marketing INTEGER NOT NULL, consent_text TEXT NOT NULL, version TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events (
          session TEXT NOT NULL, event TEXT NOT NULL, created_at TEXT NOT NULL,
          PRIMARY KEY (session,event));
        ''')
    db_path.chmod(0o600)
    csrf = secrets.token_urlsafe(32)
    limits = defaultdict(deque)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, status, body, mime='application/json', download=False):
            if mime == 'application/json': body = json.dumps(body).encode()
            elif isinstance(body, str): body = body.encode()
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' https://dermilogic.com; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if download: self.send_header('Content-Disposition', 'attachment; filename="dermilogic-preview-leads.csv"')
            self.end_headers()
            self.wfile.write(body)

        def allowed(self):
            expected = f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host') != expected or self.headers.get('Sec-Fetch-Site') == 'cross-site':
                self.send(403, {'error': 'Use the local preview address.'})
                return False
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + expected:
                self.send(403, {'error': 'This origin is not allowed.'})
                return False
            return True

        def do_GET(self):
            if not self.allowed(): return
            path = urlsplit(self.path).path
            if path == '/api/config': return self.send(200, {'csrf': csrf, 'consent': CONSENT, 'preview': True})
            if path in ('/api/leads', '/api/export'):
                if self.headers.get('X-CSRF-Token') != csrf:
                    return self.send(403, {'error': 'Open the dashboard to access leads.'})
                with sqlite3.connect(db_path) as db:
                    db.row_factory = sqlite3.Row
                    rows = [dict(row) for row in db.execute('SELECT * FROM leads ORDER BY updated_at DESC')]
                    counts = dict(db.execute('SELECT event, COUNT(*) FROM events GROUP BY event'))
                    opted = db.execute('SELECT COUNT(*) FROM leads WHERE marketing=1').fetchone()[0]
                if path == '/api/leads': return self.send(200, {'leads': rows, 'events': counts, 'opted': opted})
                output = io.StringIO()
                columns = ['email', 'created_at', 'updated_at', 'head', 'marketing', 'consent_text', 'consent_version', 'source', 'answers']
                writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()
                for row in rows:
                    writer.writerow({k: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v for k, v in row.items()})
                return self.send(200, output.getvalue(), 'text/csv; charset=utf-8', True)
            paths = {'/': 'index.html', '/admin': 'admin.html', '/app.js': 'app.js', '/admin.js': 'admin.js', '/style.css': 'style.css'}
            if path not in paths: return self.send(404, {'error': 'Page not found.'})
            file = ROOT / 'public' / paths[path]
            mime = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8'}[file.suffix]
            self.send(200, file.read_bytes(), mime)

        def do_POST(self):
            if not self.allowed(): return
            if self.headers.get('X-CSRF-Token') != csrf:
                return self.send(403, {'error': 'Refresh the page and try again.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 8192: return self.send(413, {'error': 'Request is too large or empty.'})
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict): raise ValueError('Invalid request.')
                path = urlsplit(self.path).path
                if path == '/api/recommend': return self.send(200, recommend(body.get('answers')))
                sid = body.get('session', '')
                if not isinstance(sid, str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,64}', sid): raise ValueError('Invalid session.')
                if path == '/api/events':
                    event = body.get('event')
                    if event not in ('started', 'completed', 'shop_clicked'): raise ValueError('Unknown event.')
                    with sqlite3.connect(db_path) as db:
                        db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?)', (sid, event, now()))
                    return self.send(200, {'ok': True})
                if path != '/api/leads': return self.send(404, {'error': 'Unknown endpoint.'})
                if body.get('website'): raise ValueError('Unable to save.')
                email = body.get('email', '')
                if not isinstance(email, str): raise ValueError('Invalid email.')
                email = email.strip().lower()
                if len(email) > 254 or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+", email):
                    raise ValueError('Invalid email.')
                marketing = body.get('marketing')
                if type(marketing) is not bool: raise ValueError('Invalid email preference.')
                result = recommend(body.get('answers'))
                source = body.get('source', {})
                if not isinstance(source, dict): raise ValueError('Invalid source.')
                source = {k: str(source[k])[:160] for k in ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content') if k in source}
                with lock:
                    bucket = limits[self.client_address[0]]
                    while bucket and bucket[0] < time.monotonic() - 60: bucket.popleft()
                    if len(bucket) >= 20: return self.send(429, {'error': 'Too many saves. Wait a minute and try again.'})
                    bucket.append(time.monotonic())
                stamp = now()
                with sqlite3.connect(db_path) as db:
                    db.execute('''INSERT INTO leads VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET
                    updated_at=excluded.updated_at, answers=excluded.answers, head=excluded.head,
                    marketing=excluded.marketing, consent_text=excluded.consent_text,
                    consent_version=excluded.consent_version, source=excluded.source, session=excluded.session''',
                    (email, stamp, stamp, json.dumps(body['answers']), result['key'], int(marketing), CONSENT, 'preview-v1', json.dumps(source), sid))
                    db.execute('INSERT INTO consent_history(email,recorded_at,marketing,consent_text,version) VALUES (?,?,?,?,?)', (email, stamp, int(marketing), CONSENT, 'preview-v1'))
                    db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?)', (sid, 'captured', stamp))
                self.send(200, {'ok': True, 'delivery': 'local-only'})
            except (ValueError, TypeError):
                self.send(400, {'error': 'Check your email and quiz answers, then try again.'})
            except sqlite3.Error:
                self.send(503, {'error': 'Your routine could not be saved. Please try again.'})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8891)
    parser.add_argument('--db', type=Path, default=ROOT / 'data' / 'preview.sqlite3')
    args = parser.parse_args()
    server = create_server(args.db, args.port)
    print(f'Dermilogic preview: http://127.0.0.1:{server.server_port}', flush=True)
    server.serve_forever()
