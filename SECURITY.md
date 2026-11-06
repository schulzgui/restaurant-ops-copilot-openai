# Segurança e escopo de uso

## Fronteiras de confiança

Entrada do usuário e saída do modelo são não confiáveis. O LLM não recebe ferramentas de aprovação, execução financeira, arquivos ou shell. Cada chamada passa por lista permitida, schema e regras de negócio. Aprovação exige token de revisor em rota separada. Antes de aprovar e executar, a versão do pedido é verificada.

## Controles implementados

- Tokens distintos de operador/revisor; comparação em tempo constante, sem persistência no navegador.
- Host local permitido, validação de Origin, JSON estrito, limite de corpo, CSP e ausência de CORS aberto.
- Respostas renderizadas por `textContent`, sem interpretação de HTML produzido pelo modelo.
- TLS para OpenAI e endpoint fixo; redirecionamentos recusados para impedir encaminhamento de credencial a outro destino.
- Chaves fora do código; arquivo privado com permissão POSIX 600; `.gitignore` e `.dockerignore`.
- Padrões comuns de informações sensíveis bloqueados antes da chamada de modelo. Argumentos sensíveis produzidos pelo modelo são rejeitados e redigidos no rastro.
- Erros HTTP do provedor são resumidos, sem incluir corpo, Authorization ou chave.
- Propostas idempotentes por execução/pedido/template, transações e recibo único no destino simulado.
- Nenhum request log contendo headers ou corpo é emitido pelo servidor.

## Riscos residuais

O filtro por regex não é DLP completo. Pessoas podem inserir nomes, segredos sem padrão reconhecível ou informações confidenciais no prompt; o serviço não deve ser usado com dados reais. O resumo do modelo pode ser incorreto mesmo com fontes válidas. Uma pessoa pode aprovar uma proposta inadequada. Um usuário com acesso ao sistema operacional pode ler arquivos e memória ou reescrever a cadeia de auditoria. Tokens exibidos no terminal precisam ser tratados como credenciais. O próprio provedor tem políticas de retenção independentes do cliente.

O servidor HTTP e os tokens locais não substituem autenticação empresarial, autorização granular, rate limiting por identidade, TLS público, gestão de segredos, monitoramento de abuso ou revisão profissional de segurança. Não exponha a porta publicamente.

## Incidente com credencial

Revogue a credencial no provedor, substitua-a localmente, verifique commits e artefatos publicados e investigue o uso da conta. Apagar o arquivo do último commit não remove versões anteriores do histórico. Nunca coloque segredos em uma issue de segurança. Não há programa formal de bug bounty ou garantia de segurança neste laboratório.
