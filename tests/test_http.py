import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from ops_copilot.db import Store
from ops_copilot.server import make_server
from ops_copilot.evaluation import evaluate
from helpers import ScenarioFixture

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.store=Store(Path(cls.temp.name)/"db")
        cls.server,cls.operator,cls.reviewer=make_server(cls.store,ScenarioFixture(),port=0)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f"http://127.0.0.1:{cls.server.server_port}"
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.thread.join();cls.server.server_close();cls.temp.cleanup()
    def request(self,path,body=None,token=None,extra=None):
        headers={"Content-Type":"application/json","Authorization":"Bearer "+(token or "")};headers.update(extra or {})
        req=urllib.request.Request(self.url+path,None if body is None else json.dumps(body).encode(),headers)
        with urllib.request.urlopen(req) as r:return json.load(r)
    def test_authentication(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/dashboard')
        self.assertEqual(e.exception.code,401)
    def test_role_separation(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/dispatch',{},self.operator)
        self.assertEqual(e.exception.code,403)
    def test_cross_origin_and_host(self):
        for extra in [{'Origin':'http://evil.test'},{'Host':'evil.test'}]:
            with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/run',{'prompt':'x'},self.operator,extra)
            self.assertEqual(e.exception.code,403)
    def test_static_and_traversal(self):
        with urllib.request.urlopen(self.url) as r:self.assertIn(b'Restaurant Ops Copilot',r.read())
        with self.assertRaises(urllib.error.HTTPError):self.request('/../pyproject.toml',token=self.operator)
    def test_full_workflow(self):
        r=self.request('/api/run',{'prompt':'Prepare mensagem para SYN-004'},self.operator)
        pid=r['proposal_ids'][0]
        self.request('/api/review',{'proposal_id':pid,'version':1,'decision':'approve'},self.reviewer)
        result=self.request('/api/dispatch',{},self.reviewer)
        self.assertEqual(len(result['receipts']),1)
        self.assertFalse(result['external_message_sent'])
        self.assertTrue(self.request('/api/audit',token=self.reviewer)['valid'])
    def test_empty_prompt(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/run',{'prompt':''},self.operator)
        self.assertEqual(e.exception.code,400)
    def test_evaluation(self):
        r=evaluate('data/eval_cases.json',Path(self.temp.name)/'eval.json',ScenarioFixture())
        self.assertEqual(r['n'],12)
        self.assertEqual(r['workflow_pass_rate'],1)
        self.assertEqual(r['approval_boundary_pass_rate'],1)
        self.assertEqual(r['mode'],'test_fixture')
