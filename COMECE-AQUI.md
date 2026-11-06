# Comece aqui

1. Abra o Terminal na pasta deste arquivo.
2. Execute `python3 scripts/configure.py`. Digite a chave OpenAI no campo oculto e o ID do modelo compatível. Não envie a chave no chat.
3. No macOS/Linux, execute:

```bash
export PYTHONPATH=src
python3 -m ops_copilot.cli init
python3 -m ops_copilot.cli serve
```

4. Abra http://127.0.0.1:8004. Cole o token de OPERADOR exibido no terminal no campo de acesso da página. Não compartilhe prints que mostrem tokens.
5. Peça “Prepare uma proposta para SYN-001”. Use o token REVISOR para aprovar e executar no destino local simulado.
6. Para testar a conexão real: `PYTHONPATH=src python3 scripts/live_smoke.py`.

Chamadas OpenAI podem gerar cobrança. Só use dados sintéticos. O README explica os fluxos de privacidade e os limites.

Os 34 testes locais passaram; a execução real OpenAI aguarda suas credenciais. Não há modo demo substituindo o LLM.
