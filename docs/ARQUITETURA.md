# Decisões de arquitetura

## LLM obrigatório e efeitos restritos

A Responses API escolhe ferramentas e sintetiza o resultado. Não há um roteador determinístico substituindo o modelo no caminho da aplicação. Regras determinísticas existem para impor permissões, disponibilidade dos dados e validade das ações. O backend monta mensagens de templates para impedir promessas financeiras ou de prazo não confirmadas.

## Orquestração com orçamento

O histórico da execução preserva todos os itens de output, incluindo reasoning, e acrescenta cada function_call_output com call_id correspondente. Há máximo de 12 etapas, 16 ferramentas e três pedidos propostos. Timeout e retries limitam falhas transitórias. Falha não vira resposta demonstrativa: o run fica failed; propostas já criadas continuam pendentes de revisão, sem execução automática.

## Evidência consultada

Um conjunto em memória registra os pedidos e políticas retornados nesta execução. propose_action exige os dois IDs nesse conjunto e valida a combinação contra o estado atual. Structured Outputs exige o schema de resumo; a aplicação verifica tipos e se os IDs citados foram realmente consultados. Isso valida procedência, não a verdade semântica de toda frase.

## Concorrência e revisão

SQLite com WAL permite leituras concorrentes; BEGIN IMMEDIATE serializa mutações. A chave de proposta identifica execução + pedido + template + política. Repetir a ferramenta na mesma execução reutiliza o registro. Uma nova solicitação cria novo run e pode criar nova proposta; não há deduplicação semântica de solicitações distintas.

A revisão usa versionamento otimista. Um pedido alterado invalida aprovação de proposta antiga. A execução confere novamente a versão e marca itens obsoletos como stale. Propostas rejeitadas não entram na outbox.

## Outbox e destino

A aprovação insere a outbox na mesma transação da decisão. O worker local grava recibo e marca entrega na mesma transação; a chave única impede dois recibos para a mesma proposta. Essa atomicidade vale porque o destino é o mesmo SQLite. Uma integração real exigiria chave idempotente no serviço externo, recuperação de leases e confirmação de entrega. Não alegamos exactly-once distribuído.

Falhas do sink podem ser injetadas por `Store.dispatch(fail=True)` nos testes. Após três falhas o item passa a dead_letter. A rota de requeue exige papel revisor. Não há loop automático do worker; a UI ou `worker` dispara uma rodada limitada a 20 itens.

## Auditoria

Eventos têm JSON canônico, hash anterior e SHA256. A verificação detecta adulteração de um evento sem recomputar a cadeia. Ela não protege contra um administrador que reescreva toda a cadeia. Não existe assinatura externa ou ancoragem em outro serviço.

## Implantação

A aplicação serve localmente, sem dependências Python de runtime. Um contêiner oferece ambiente isolado de execução, mas não transforma o servidor em um serviço público seguro. Para operação empresarial: servidor adequado, identidade, autorização por empresa, banco gerenciado, migrações, backup, políticas de retenção e observabilidade externa.
