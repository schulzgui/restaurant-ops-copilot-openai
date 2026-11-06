# Publicar com cuidado

1. Crie um repositório vazio chamado restaurant-ops-copilot. Não copie o banco runtime ou arquivos de credencial.
2. Execute os testes e `python3 scripts/check_release.py` na raiz.
3. Inicialize o Git, confira os arquivos e envie:

```bash
git init -b main
git add .
git diff --cached --name-only
python3 scripts/check_release.py
git commit -m "Add LLM operations copilot with supervised workflows"
git remote add origin https://github.com/SEU_USUARIO/restaurant-ops-copilot.git
git push -u origin main
```

Se `.secrets.json`, `.env`, arquivos SQLite ou `runtime/` aparecerem na lista, pare e remova-os da área de staging antes do commit. Não ignore uma falha do verificador de release. A verificação por padrões não substitui sua revisão.

4. Confira a aba Actions. O workflow não usa credenciais OpenAI e não roda avaliações pagas automaticamente.
5. Se publicar relatórios live, revise todo o conteúdo; eles ficam ignorados por padrão. Nunca envie sua configuração privada como solução de erro de autenticação.
6. Grave uma demonstração sem mostrar tokens do terminal ou a chave. O relatório deve indicar o modelo utilizado e distinguir execução de LLM de testes com fixtures.

GitHub Pages não executa este backend. Para apresentar, execute localmente ou use uma implantação autenticada e revisada; não exponha o servidor padrão à internet.
