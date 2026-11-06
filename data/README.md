# Data card

Todos os registros foram gerados para este laboratório, sob licença MIT. Não há dados de clientes reais nem vínculo com o iFood.

- `orders.json`: 60 pedidos com ID SYN, status, atraso em minutos, tipo de ocorrência, valor fictício e versão. Semente 42; cinco casos iniciais fixados para demonstração. O valor não é usado para decisões financeiras.
- `policies.json`: quatro políticas fictícias (atraso, segurança alimentar, item ausente e revisão), versão 1. Nenhuma validade contratual.
- `eval_cases.json`: 12 cenários manuais, incluindo consulta, proposta, pedido inexistente, cancelado, assunto fora de escopo e tentativas de aprovação/reembolso.

O SQLite é inicializado diretamente pelo gerador `seed.py`; os JSONs são uma exportação auditável das fixtures. Editar somente os JSONs de pedidos/políticas não altera o banco nem as regras. `init` preserva pedidos já existentes.

Vieses: poucos estados, políticas curtas, sem calendário, rota, cadastro de cliente ou cenário real de restaurante. A avaliação foi escrita junto ao projeto, não por terceiros independentes.
