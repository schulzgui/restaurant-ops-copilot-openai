# API HTTP

Base local: `http://127.0.0.1:8004`. Todas as rotas `/api/*` exigem `Authorization: Bearer TOKEN`. POST usa `Content-Type: application/json`; máximo 16 KiB. Header Host deve apontar para localhost ou 127.0.0.1 na porta atual.

| Método | Rota | Papel | Corpo / resultado |
|---|---|---|---|
| GET | /health | Público | status, modo, identificação sintética |
| GET | /api/dashboard | Ambos | pedidos, propostas, 20 runs recentes, outbox, recibos |
| GET | /api/audit | Ambos | verificação da cadeia e eventos |
| POST | /api/run | Operador | `{"prompt":"Prepare proposta para SYN-001"}` |
| POST | /api/review | Revisor | `{"proposal_id":"ID","decision":"approve","version":1}` |
| POST | /api/dispatch | Revisor | `{}`; cria recibos apenas no sink simulado |
| POST | /api/requeue | Revisor | `{"proposal_id":"ID"}`; apenas dead_letter |

`decision` aceita approve ou reject. A identidade registrada é reviewer-local, vinculada ao papel compartilhado; não equivale a um usuário autenticado por SSO.

Códigos: 400 entrada/transição inválida; 401 credencial ausente/incorreta; 403 papel, origem ou host inválido; 404 rota ausente; 408 leitura expirou; 413 tamanho inválido; 415 conteúdo não JSON; 429 duas análises simultâneas em curso. Um run que falha no provedor retorna objeto HTTP 200 com `status=failed`: o consumidor deve verificar esse campo.

A saída de run contém id, mode, status, answer, final (quando válido), trace, sources, proposal_ids, tokens e duração. Valores monetários não são estimados sem configuração de preço; `cost_usd` é null.

O modelo não recebe rotas HTTP de revisão/execução como ferramentas. Não aceite token HTTP fornecido pelo texto do prompt.
