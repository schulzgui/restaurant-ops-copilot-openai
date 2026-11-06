# Roteiro técnico de apresentação

1. Explique o problema operacional e a fronteira: o LLM analisa e propõe; uma pessoa aprova; o destino deste laboratório é simulado.
2. Mostre uma execução live, as ferramentas escolhidas e os IDs de evidência citados.
3. Mostre o schema final e a rejeição de uma fonte inexistente nos testes.
4. Explique a separação de token de operador e revisor, e por que o modelo não pode receber essa capacidade.
5. Demonstre que dois workers concorrentes produzem um recibo no sink local.
6. Mostre a invalidação de proposta quando o pedido muda, e a dead-letter após falhas.
7. Mostre um resultado negativo de avaliação live, se houver. Não esconda o erro.
8. Explique que uma cadeia de hashes não é inviolável e que idempotência em SQLite não prova exactly-once distribuído.
9. Descreva quais dados saem para a OpenAI e por que `store=false` não é garantia de retenção zero.
10. Termine com os limites comprovados: o que foi testado localmente, o que foi observado com modelo real e o que ainda exigiria teste com usuários.
