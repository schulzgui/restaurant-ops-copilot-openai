"""Inspect tracked files when Git exists, otherwise the distributable allowlist."""
import re
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
try:
    result=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=root,capture_output=True,text=True,check=True)
    if Path(result.stdout.strip()).resolve()!=root:raise ValueError('Not project root')
    names=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    paths=[root/n for n in names if n]
except (subprocess.CalledProcessError,ValueError):
    paths=[p for p in root.rglob('*') if p.is_file() and not any(x in p.relative_to(root).parts for x in ['.git','__pycache__','.venv','runtime'])]
issues=[]
for p in paths:
    name=p.relative_to(root).as_posix()
    if p.name=='.secrets.json' or p.name.startswith('.env') or '.sqlite' in p.name:
        issues.append(name+': private file')
    if p.suffix in {'.pyc','.png','.zip'}:continue
    try:text=p.read_text(encoding='utf-8')
    except UnicodeDecodeError:continue
    # Explicit fixture credentials in tests are harmless; production/distributable texts are scanned.
    if not name.startswith('tests/'):
        for pattern in [r'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']:
            if re.search(pattern,text):issues.append(name+': possible secret')
if issues:raise SystemExit('\n'.join(issues))
print('Release scan passed:',len(paths),'files inspected. Pattern scan is not an absolute security guarantee.')
