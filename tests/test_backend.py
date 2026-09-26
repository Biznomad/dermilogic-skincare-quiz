import itertools
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import create_server, recommend, OPTIONS

class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=Path(self.temp.name)/'test.sqlite3'
        self.server=create_server(self.db,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.token=self.request('/api/config')[1]['csrf']
        self.payload={'session':'test-session-123456789','email':'test@example.com','marketing':False,'answers':{'concern':'spots','feel':'oily','sensitivity':'comfortable','routine':'basic','spf':'sometimes'},'source':{'utm_source':'test','utm_campaign':'routine'}}

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.temp.cleanup()

    def request(self,path,body=None,headers=None):
        base_headers={'Content-Type':'application/json','X-CSRF-Token':getattr(self,'token','')}
        base_headers.update(headers or {})
        req=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=base_headers)
        try: response=urllib.request.urlopen(req)
        except urllib.error.HTTPError as error: response=error
        content=response.read().decode()
        return response.status,json.loads(content) if response.headers.get_content_type()=='application/json' else content

    def test_every_recommendation_path(self):
        for values in itertools.product(*(OPTIONS[k] for k in OPTIONS)):
            answers=dict(zip(OPTIONS,values)); result=recommend(answers)
            care=answers['concern']=='painful' or answers['sensitivity']=='irritated' or answers['routine']=='prescribed'
            self.assertEqual(result['care'],care)
            if care:
                self.assertEqual(result['shop'],'https://find-a-derm.aad.org/')
            else:
                self.assertNotIn('brush',result['shop'])
                self.assertEqual(len(result['steps']),3)
                self.assertIn('Moisturizer and sunscreen',result['gap'])
            self.assertIn('SPF 30',result['steps'][2][1])
            if answers['sensitivity']=='reactive': self.assertNotEqual(result['name'],'Pimple Rescue Patches')

    def test_capture_dedup_and_consent_history(self):
        self.assertEqual(self.request('/api/leads',self.payload)[0],200)
        self.payload.update(email=' TEST@EXAMPLE.COM ',marketing=True)
        self.assertEqual(self.request('/api/leads',self.payload)[0],200)
        data=self.request('/api/leads')[1]
        self.assertEqual(len(data['leads']),1); self.assertEqual(data['opted'],1)
        self.assertEqual(data['events']['captured'],1)
        self.payload['marketing']=False
        self.request('/api/leads',self.payload)
        self.assertEqual(self.request('/api/leads')[1]['opted'],0)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM consent_history').fetchone()[0],3)

    def test_invalid_capture_rejected(self):
        for key,value in [('email','broken'),('marketing','true'),('answers',{}),('session','short'),('website','spam')]:
            with self.subTest(key=key):
                self.assertEqual(self.request('/api/leads',dict(self.payload,**{key:value}))[0],400)
        self.assertEqual(len(self.request('/api/leads')[1]['leads']),0)

    def test_origin_host_csrf_and_private_files(self):
        self.assertEqual(self.request('/api/leads',self.payload,{'X-CSRF-Token':'wrong'})[0],403)
        self.assertEqual(self.request('/api/config',headers={'Origin':'https://other.example'})[0],403)
        self.assertEqual(self.request('/api/config',headers={'Host':'rebound.example'})[0],403)
        self.assertEqual(self.request('/api/config',headers={'Sec-Fetch-Site':'cross-site'})[0],403)
        self.assertEqual(self.request('/api/leads',headers={'X-CSRF-Token':''})[0],403)
        self.assertEqual(self.request('/data/preview.sqlite3')[0],404)

    def test_export_is_formula_safe_and_preserves_source(self):
        self.payload['email']='=test@example.com'
        self.request('/api/leads',self.payload)
        status,body=self.request('/api/export')
        self.assertEqual(status,200); self.assertIn("'=test@example.com",body)
        self.assertIn('routine',body); self.assertIn('preview-v1',body)

    def test_event_dedup(self):
        for _ in range(2): self.request('/api/events',{'session':self.payload['session'],'event':'started'})
        self.assertEqual(self.request('/api/leads')[1]['events']['started'],1)
        self.assertEqual(self.request('/api/events',{'session':self.payload['session'],'event':'captured'})[0],400)

    def test_rate_limit(self):
        for _ in range(20): self.assertEqual(self.request('/api/leads',self.payload)[0],200)
        self.assertEqual(self.request('/api/leads',self.payload)[0],429)

if __name__=='__main__': unittest.main()
