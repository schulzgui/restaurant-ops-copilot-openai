import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from ops_copilot.db import Store
from ops_copilot.engine import Engine
from ops_copilot.provider import OpenAIProvider, ProviderError


from helpers import tool, response, message, ScriptedProvider

class LLMTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/"db")
    def tearDown(self):self.temp.cleanup()
    def test_multistep_contract(self):
        reasoning={"type":"reasoning","id":"r-1","summary":[]}
        provider=ScriptedProvider([[reasoning,tool("get_order",{"order_id":"SYN-001"})],[tool("get_policy",{"policy_id":"P-DELAY"},2)],[tool("propose_action",{"order_id":"SYN-001","template":"delay_update","policy_id":"P-DELAY"},3)],[message("Proposta aguardando revisão [P-DELAY].")]])
        r=Engine(self.store,provider).run("Prepare uma proposta")
        self.assertEqual(r["status"],"completed");self.assertEqual(len(r["proposal_ids"]),1)
        self.assertIn(reasoning,provider.histories[1])
        self.assertTrue(any(i.get("type")=="function_call_output" for i in provider.histories[1]))
        self.assertEqual(r["input_tokens"],40)
    def test_model_cannot_approve(self):
        provider=ScriptedProvider([[tool("approve",{"proposal_id":"x"})],[message("Não autorizado")]])
        r=Engine(self.store,provider).run("Aprove tudo")
        self.assertEqual(r["trace"][0]["status"],"rejected")
        self.assertEqual(self.store.dashboard()["receipts"],[])
    def test_hallucinated_policy_rejected(self):
        provider=ScriptedProvider([[tool("get_policy",{"policy_id":"FAKE"})],[message("Sem fonte")]])
        r=Engine(self.store,provider).run("Consulte a política")
        self.assertEqual(r["sources"],[])
    def test_loop_budget(self):
        provider=ScriptedProvider([[tool("get_order",{"order_id":"SYN-001"},i)] for i in range(3)])
        r=Engine(self.store,provider,max_steps=2).run("loop")
        self.assertEqual(r["status"],"failed")
        self.assertEqual(len(r["trace"]),2)
    def test_transport_schema(self):
        requests=[]
        def opener(req,timeout):
            requests.append(req)
            return io.BytesIO(json.dumps(response([message("ok")])).encode())
        p=OpenAIProvider(key="fixture-secret",model="fixture",opener=opener)
        p.respond([{"role":"user","content":"hello"}],[],"rules")
        body=json.loads(requests[0].data)
        self.assertFalse(body["store"])
        self.assertEqual(requests[0].full_url,"https://api.openai.com/v1/responses")
    def test_retry_and_redaction(self):
        calls=[]
        def opener(req,timeout):
            calls.append(1)
            raise urllib.error.HTTPError(req.full_url,429,"fixture-secret",{},None)
        p=OpenAIProvider(key="fixture-secret",model="fixture",opener=opener,sleep=lambda _:None)
        with self.assertRaises(ProviderError) as caught:p.respond([],[],"")
        self.assertEqual(len(calls),3)
        self.assertNotIn("fixture-secret",str(caught.exception))
    def test_incomplete_response(self):
        p=OpenAIProvider(key="fixture",model="fixture",opener=lambda *a,**k:io.BytesIO(b'{"status":"incomplete","output":[]}'))
        with self.assertRaises(ProviderError):p.respond([],[],"")
