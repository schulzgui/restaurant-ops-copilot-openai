import tempfile
import unittest
from pathlib import Path
from ops_copilot.privacy import check_text
from ops_copilot.domain import DomainError
from ops_copilot.db import Store
from ops_copilot.engine import Engine
from ops_copilot.provider import NoRedirect, ProviderError
from helpers import ScenarioFixture, ScriptedProvider, tool, message

class PrivacyTests(unittest.TestCase):
    def test_common_sensitive_patterns(self):
        samples=['email@example.test','123.456.789-01','sk-testcredential123456','Bearer token0123456789','-----BEGIN PRIVATE KEY-----','4111 1111 1111 1111']
        for sample in samples:
            with self.subTest(sample=sample),self.assertRaises(DomainError):check_text(sample)
    def test_safe_ids(self):check_text('Prepare proposta para SYN-001 com atraso de 12 minutos')
    def test_rejection_before_provider_and_storage(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d)/'db')
            provider=ScriptedProvider([])
            with self.assertRaises(DomainError):Engine(store,provider).run('sk-testcredential123456')
            self.assertEqual(provider.histories,[])
            self.assertEqual(store.dashboard()['runs'],[])
    def test_redirect_blocked(self):
        with self.assertRaises(ProviderError):NoRedirect().redirect_request(None,None,302,'redirect',{},'https://evil.test')
    def test_model_sensitive_argument_not_logged(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d)/'db')
            provider=ScriptedProvider([[tool('search_policies',{'query':'sk-testcredential123456'})],[message('Bloqueado')]])
            r=Engine(store,provider).run('Busque políticas')
            self.assertEqual(r['trace'][0]['arguments'],{'redacted':True})
            self.assertNotIn('sk-testcredential123456',str(store.dashboard()))
    def test_fake_citation_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            provider=ScriptedProvider([[message('Conclusão',policies=['P-FAKE'])]])
            r=Engine(Store(Path(d)/'db'),provider).run('Consulte políticas')
            self.assertEqual(r['status'],'failed')
