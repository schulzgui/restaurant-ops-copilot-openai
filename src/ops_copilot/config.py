"""Read only the private configuration explicitly created for this project."""
import json
import os
from pathlib import Path

ALLOWED={"OPENAI_API_KEY","OPENAI_MODEL","OPS_OPERATOR_TOKEN","OPS_REVIEWER_TOKEN"}
def load_local(path=".secrets.json"):
    p=Path(path)
    if not p.exists():return
    if os.name=="posix" and p.stat().st_mode & 0o077:
        raise ValueError("Arquivo .secrets.json deve ter permissão 600")
    obj=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj,dict) or set(obj)-ALLOWED or any(not isinstance(v,str) for v in obj.values()):
        raise ValueError("Configuração local inválida")
    for key,value in obj.items():os.environ.setdefault(key,value)
