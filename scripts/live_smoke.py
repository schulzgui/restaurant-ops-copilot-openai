"""Owner-triggered paid API smoke test, with synthetic data in a temporary DB."""
import json
import tempfile
from pathlib import Path
from ops_copilot.config import load_local
from ops_copilot.db import Store
from ops_copilot.engine import Engine
from ops_copilot.provider import OpenAIProvider
load_local()
with tempfile.TemporaryDirectory() as d:
    store=Store(Path(d)/'smoke.sqlite')
    run=Engine(store,OpenAIProvider()).run('Consulte SYN-001 e a política de atraso. Prepare uma proposta adequada, sem aprovar nem executar.')
    result={'status':run['status'],'mode':run['mode'],'model':run.get('model'),'tool_calls':[t['tool'] for t in run['trace']],'proposals':len(run['proposal_ids']),'input_tokens':run['input_tokens'],'output_tokens':run['output_tokens'],'duration_ms':run['duration_ms'],'external_messages':len(store.dashboard()['receipts'])}
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/live-smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if run['status']!='completed' or len(run['proposal_ids'])!=1 or result['external_messages']!=0:raise SystemExit(1)
