# Fluxo de dados

| Informação | Destino | Persistência no aplicativo |
|---|---|---|
| Chave OpenAI | Header HTTPS para api.openai.com/v1/responses | Ambiente ou .secrets.json privado |
| Tokens de papéis | API local | Ambiente/arquivo privado; memória do navegador após login |
| Prompt | OpenAI | Não há coluna de prompt bruto; partes podem aparecer em argumentos e resumo |
| Pedidos/políticas consultados | OpenAI e interface local | Fixtures e SQLite |
| Resposta validada e chamadas | Interface local | Tabela runs no SQLite |
| Propostas e decisões | API local e SQLite | Auditoria e outbox |
| Recibos | Somente SQLite local | Não existe envio a clientes |

A aplicação não faz telemetria, analytics, carregamento de fontes remotas ou chamadas a URLs arbitrárias. O endpoint OpenAI é fixo. Ferramentas não podem ler arquivos, variáveis de ambiente nem consultar outro serviço. Uma chamada live envia contexto à OpenAI; isso deve ser entendido antes de usar a aplicação.

`store=false` é um parâmetro de requisição, não uma declaração de retenção zero. Consulte as condições atuais do provedor e sua conta antes de usar dados que tenham qualquer restrição.

A verificação de release procura arquivos privados e padrões de chave em arquivos distribuíveis. Ela não prova que um repositório está livre de toda informação sensível. O arquivo de banco, `.secrets.json`, `.env` e relatórios live são excluídos dos pacotes por padrão.

Para apagar dados de uma demonstração, encerre o servidor e remova apenas o diretório runtime criado por este projeto, se não precisar do histórico. Em Docker, apagar o volume elimina o banco. A remoção local não remove dados já processados pelo provedor.
