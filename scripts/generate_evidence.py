"""Offline software-contract evidence, explicitly NOT LLM performance."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from helpers import ScenarioFixture
from ops_copilot.evaluation import evaluate
r=evaluate('data/eval_cases.json','artifacts/contract-evaluation.json',ScenarioFixture())
print('Contract fixture:',r['n'],'cases;',r['workflow_pass_rate'],'pass rate. Not live LLM evaluation.')
