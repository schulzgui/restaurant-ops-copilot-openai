"""Run by the owner in a local terminal. Never paste credentials into chat."""
import getpass
import json
import os
import secrets
from pathlib import Path

path=Path('.secrets.json')
if path.exists():
    raise SystemExit('Configuração já existe. Edite-a localmente ou remova-a explicitamente antes de reconfigurar.')
key=getpass.getpass('Chave OpenAI (entrada oculta): ').strip()
model=input('ID do modelo OpenAI com Responses, function calling e Structured Outputs: ').strip()
if not key or not model:raise SystemExit('Chave e modelo são obrigatórios.')
values={'OPENAI_API_KEY':key,'OPENAI_MODEL':model,'OPS_OPERATOR_TOKEN':secrets.token_urlsafe(24),'OPS_REVIEWER_TOKEN':secrets.token_urlsafe(24)}
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(values,f)
print('Configuração salva localmente em .secrets.json (ignorada pelo Git). Nenhuma chamada à API foi feita.')
