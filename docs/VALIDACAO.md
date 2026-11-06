# Validação executada — 6 de novembro de 2026

| Verificação | Resultado |
|---|---|
| Testes locais de domínio, concorrência, contrato LLM, privacidade e API HTTP | 34 aprovados |
| Cenários de contrato com provedor controlado | 12/12 passaram; não são métricas de um LLM |
| Inicialização e preservação da base | Testadas |
| Encadeamento de auditoria e detecção de adulteração | Testados |
| Aprovação, versões, idempotência e dead-letter | Testados |
| Bloqueio de dados sensíveis nos padrões cobertos | Testado; não garante DLP universal |
| Verificação de arquivos de distribuição | Aprovada para padrões verificados |
| Execução real OpenAI | Não executada: credenciais/modelo serão configurados pelo usuário |
| Build/execução Docker e CI remota | Não executados neste ambiente |
| Inspeção visual em navegador | Não executada; endpoints HTTP testados |
| Piloto com usuários e impacto de negócio | Não realizados |

[Saída dos testes](../artifacts/tests.txt). [Avaliação de contrato](../artifacts/contract-evaluation.json).

O programa exige um provedor LLM. Sem credenciais, a CLI informa o requisito e não gera uma análise fictícia. Os provedores controlados estão em tests/helpers.py e só são utilizados pelos testes e pelo script de evidência de contrato.

Para validar o caminho real, configure scripts/configure.py e rode scripts/live_smoke.py. Consulte README para comandos completos. Não confundir implementação concluída com operação em produção validada.
