import concurrent.futures
import json
import tempfile
import unittest
from pathlib import Path
from ops_copilot.db import Store
from ops_copilot.domain import DomainError
from ops_copilot.engine import Engine
from ops_copilot.tools import ToolRunner

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "db.sqlite"
        self.store = Store(self.path)
    def tearDown(self):
        self.temp.cleanup()
    def proposal(self, key="one"):
        return self.store.propose("SYN-001", "delay_update", "P-DELAY", key)
    def test_seed_is_preserved_on_restart(self):
        self.store.update_order("SYN-001", delay_minutes=15)
        self.assertEqual(Store(self.path).order("SYN-001")["delay_minutes"], 15)
    def test_evidence_gate(self):
        runner = ToolRunner(self.store, "r")
        with self.assertRaises(DomainError):
            runner.call("propose_action", {"order_id":"SYN-001","template":"delay_update","policy_id":"P-DELAY"})
    def test_invalid_policy_and_template(self):
        with self.assertRaises(DomainError):
            self.store.propose("SYN-003", "delay_update", "P-DELAY", "bad")
        self.assertEqual(self.store.proposals(), [])
    def test_unknown_and_additional_tool_args(self):
        runner = ToolRunner(self.store, "r")
        for name,args in [("approve",{}),("get_order",{"order_id":"SYN-001","sql":"DROP TABLE orders"})]:
            with self.assertRaises(DomainError):runner.call(name,args)
    def test_idempotency_and_conflict(self):
        p = self.proposal()
        self.assertEqual(p, self.proposal())
        with self.assertRaises(DomainError):
            self.store.propose("SYN-002", "escalate", "P-DELAY", "one")
        self.assertEqual(self.store.audit()["events"], 1)
    def test_concurrent_proposals(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.proposal(), range(16)))
        self.assertEqual(len({p["id"] for p in results}),1)
        self.assertEqual(len(self.store.proposals()),1)
    def test_approval_required_and_once_delivery(self):
        p = self.proposal()
        self.assertEqual(self.store.dispatch(),[])
        self.store.review(p["id"], "approve", "human", 1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _:self.store.dispatch(),range(8)))
        self.assertEqual(sum(map(len,results)),1)
        self.assertEqual(len(self.store.dashboard()["receipts"]),1)
        self.assertFalse(self.store.dashboard()["receipts"][0]["external_message_sent"])
    def test_stale_review(self):
        p=self.proposal();self.store.update_order("SYN-001",status="delivered")
        with self.assertRaises(DomainError):self.store.review(p["id"],"approve","human",1)
    def test_stale_dispatch(self):
        p=self.proposal();self.store.review(p["id"],"approve","human",1)
        self.store.update_order("SYN-001",status="cancelled")
        self.assertEqual(self.store.dispatch(),[])
        self.assertEqual(self.store.dashboard()["outbox"][0]["state"],"stale")
    def test_rejected_and_repeated_review(self):
        p=self.proposal();self.store.review(p["id"],"reject","human",1)
        with self.assertRaises(DomainError):self.store.review(p["id"],"approve","human",2)
        self.assertEqual(self.store.dispatch(),[])
    def test_dead_letter_and_manual_requeue(self):
        p=self.proposal();self.store.review(p["id"],"approve","human",1)
        for _ in range(3):self.store.dispatch(fail=True)
        self.assertEqual(self.store.dashboard()["outbox"][0]["state"],"dead_letter")
        self.assertEqual(self.store.dispatch(),[])
        self.store.requeue(p["id"],"human")
        self.assertEqual(len(self.store.dispatch()),1)
    def test_audit_detects_tampering(self):
        self.proposal();self.assertTrue(self.store.audit()["valid"])
        with self.store.connection() as db:db.execute("UPDATE audit SET body='tampered' WHERE seq=1")
        self.assertFalse(self.store.audit()["valid"])
    def test_llm_is_required(self):
        with self.assertRaises(ValueError):Engine(self.store,None)
    def test_llm_contract_end_to_end(self):
        from helpers import ScenarioFixture
        r=Engine(self.store,ScenarioFixture()).run("Prepare uma mensagem para SYN-003")
        self.assertEqual(r["sources"],["P-SAFETY"])
        self.assertEqual(len(r["proposal_ids"]),1)
        self.assertEqual(self.store.proposals()[0]["priority"],"urgent")
        self.assertTrue(self.store.audit()["valid"])
