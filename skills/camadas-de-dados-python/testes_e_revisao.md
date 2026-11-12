# Testes e revisão

[← SKILL.md](SKILL.md)

## Anti-padrões

- Um único modelo para entrada, banco e resposta.
- `dict` solto atravessando camadas ("saco de dados").
- Validar no meio do núcleo, de novo e de novo.
- Regra só no prompt, só no `description` ou só num comentário.
- `Any` e `extra="allow"` na borda sem motivo registrado.
- `except Exception: pass` em parsing.
- Enum cujo valor é texto de exibição (muda com a interface; o valor deveria ser estável).
- `__post_init__` fazendo papel de validação de entrada externa.

## Estratégia de testes

- **Cobertura de enums:** toda tabela indexada por enum cobre todos os membros.
- **Matriz de política:** perfil × ação → decisão esperada.
- **Ida e volta:** `Modelo.model_validate(obj.model_dump(mode="json")) == obj`.
- **Uma pegadinha por teste:** cada item relevante do catálogo vira um teste que falharia sem o remédio.
- **Mensagens, não ordem:** compare conjuntos de erros (`{(e["loc"], e["type"]) for e in ex.errors()}`).
- **LLM offline:** cliente simulado com a interface do SDK (`.chat.completions.create` devolvendo os tipos do SDK) e roteiros que erram de propósito.
- **LLM real:** conjunto de avaliação com gabarito; medir taxa de acerto; gravar respostas reais para regressão.
- **Versões:** rodar a suíte em duas versões do Pydantic quando o comportamento importa.

## Checklist de revisão

- [ ] Cada dado tem origem clara e a ferramenta certa (borda x núcleo).
- [ ] Entradas externas com `extra="forbid"` (ou motivo registrado para não).
- [ ] Vocabulários fechados são enums; valores tratados como contrato externo.
- [ ] Normalização em `BeforeValidator`; regras em `AfterValidator`/`model_validator`.
- [ ] Regras dependentes do pedido usam `context=` e falham sem contexto.
- [ ] Dinheiro em `Decimal`, construído de texto.
- [ ] Núcleo em dataclasses; frozen onde não muda; coleções internas protegidas.
- [ ] Tabelas por enum com teste de cobertura; `match` com `case _`.
- [ ] Permissões negam por padrão; perfil vem da sessão.
- [ ] Segredos em `SecretStr`; nunca em logs, `repr` ou JSON.
- [ ] Erros de validação viram mensagens úteis (para usuário ou LLM).
- [ ] Logs e JSONL sem dados sensíveis e sem códigos de cor.
- [ ] Testes cobrem as pegadinhas relevantes; o que não foi testado está dito.
