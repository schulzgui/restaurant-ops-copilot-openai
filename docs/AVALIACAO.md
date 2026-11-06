# Protocolo de avaliação

## Contratos sem rede

`python -m unittest discover -s tests -v` testa regras, transações, falhas, concorrência, transporte, schema, fronteiras de autorização e proteções de privacidade. O provedor controlado existe em tests/helpers.py. Ele não é um modelo e não pode ser selecionado pela CLI da aplicação.

`generate_evidence.py` executa 12 casos com esse provedor e grava `mode=test_fixture`. A taxa de passagem mede apenas o comportamento do software diante das respostas controladas. Não é uma comparação entre modelos e não sustenta alegações de acurácia de IA.

## Execução live

Configure suas credenciais e rode `scripts/live_smoke.py`, depois `ops_copilot.cli evaluate`. Cada caso usa um banco temporário independente. Há chamadas pagas. O relatório contém o modelo efetivamente usado, tokens, latência observada, ferramentas e resultados. Falhas são mantidas.

Os 12 cenários têm expectativas de templates e ferramentas mínimas. O avaliador verifica o multiconjunto de templates, presença das tentativas de ferramentas exigidas, conclusão do run e ausência de recibos/ações aprovadas. Não avalia sozinho qualidade textual, tom, utilidade, alucinação semântica ou satisfação do usuário. O caso de pedido inexistente exige tentativa de consulta, mesmo que a ferramenta rejeite o ID.

## Revisão humana sugerida

Depois de uma execução live, revise respostas e evidências com rubrica: fato correto, fonte relevante, nenhuma promessa indevida, próximo passo útil, interpretação correta da intenção. Registre avaliador e justificativa sem dados pessoais. Amplie os casos com autoria independente antes de estimar generalização.

Não há piloto com usuários, ganho de horas medido, fine-tuning, comparação de modelos ou garantia estatística neste pacote. UUIDs, timestamps, latência e respostas live variam; a reprodutibilidade aqui significa protocolo, fixtures e código disponíveis, não igualdade textual do LLM.
