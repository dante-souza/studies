# AI Use Cases — trilha com LLM

Um único exemplo do começo ao fim: um **assistente de lista de compras**. A cada notebook ele ganha uma garantia nova, e
cada notebook termina mostrando **o que ainda quebra**: é esse problema que o próximo resolve.

```
01_basico/          chamadas REAIS à API, código direto
  01 chamada e JSON           → a resposta é texto; o JSON pedido no prompt não tem garantia
  02 saída estruturada        → contrato Pydantic: campos e tipos
  03 enums e guardrails       → vocabulário fechado (Unidade, Categoria) e escopo (TipoPedido)

02_intermediario/   chamadas REAIS à API + funções simples
  04 ferramentas com funções  → o modelo pede, o código executa (com guardrail)
  05 regras e retry           → regras de negócio + erro devolvido ao modelo
  06 roteamento por enum      → intenção → rota → ferramentas permitidas

03_avancado/        modelo SIMULADO no formato da OpenAI (roda offline, testável)
  07 contrato e contexto      → regras dentro do contrato, com orçamento/despensa/preços
  08 capacidades e políticas  → quem pode o quê (Flag), negar por padrão, confirmação humana
  09 runtime com dataclasses  → histórico com orçamento de tokens, custo em Decimal, tempo
  10 pipeline completo        → settings do ambiente, cache, log sem dados sensíveis, testes
```

## Os ganchos

| De | O que quebrou | Para | Como resolve |
|---|---|---|---|
| 01 | `"250 grams" * 2` vira texto repetido; formato sem garantia | 02 | contrato Pydantic com `quantidade: float` |
| 02 | `unidade: str` aceita `"cups"` | 03 | `Unidade(StrEnum)` |
| 03 | 3 kg de sal para 2 pessoas passa; o modelo não sabe preços | 04 | ferramentas com dados reais |
| 04 | a lista final ainda não é conferida | 05 | regras + retry |
| 05 | regras fora do contrato, sem contexto | 07 | `model_validator` com `context=` |
| 06 | permissões e valores desconhecidos | 08 | `Flag`, `decidir`, enum aberto |
| 08 | fluxo opaco: tokens, custo, tempo, histórico crescendo | 09 | dataclasses de runtime |
| 09 | configuração de fora sem validação; peças soltas | 10 | `BaseSettings` + pipeline |

## Configurando a API (básico e intermediário)

As células que chamam a API seguem o mesmo molde: chave e endpoint lidos do `.env` com `python-dotenv`.

```bash
cp .env.example .env      # nesta pasta ou na raiz do repositório
# edite: openai=<sua chave>   openai_base_url=<endpoint compatível com a OpenAI>
```

O `.env` **não vai para o git** (está no `.gitignore`). O `load_dotenv()` procura o arquivo subindo a partir da pasta do notebook.

## O que roda sem chave

- As células de API começam com `# api:` e têm a tag `skip-execution`. **Não foram executadas** ao salvar estes notebooks,
  porque o ambiente de geração não tem acesso ao seu endpoint. Com o `.env` configurado, rode-as normalmente.
- Todo o resto foi **executado** e está salvo com as saídas. Onde a lógica precisa de uma resposta de modelo, ela vem de:
  - [`respostas_gravadas/`](respostas_gravadas/README.md): respostas **reais** da API, sem alteração;
  - exemplos marcados como *exemplo construído* ou *roteiro construído*, no formato que o modelo devolveria. Não são saídas reais.
- No avançado, o [`llm_simulado.py`](03_avancado/llm_simulado.py) imita o cliente `OpenAI(...)` e devolve objetos do próprio SDK.
  O notebook 10 mostra a troca pelo cliente real em uma linha.
- `jupyter nbconvert --execute` pula as células `skip-execution` (testado). No Jupyter, "Run All" **sem** `.env` para na primeira
  célula de configuração. Nesse caso, rode célula a célula ou configure o `.env`.

## Módulos de apoio

| Arquivo | O que é |
|---|---|
| [`02_intermediario/contrato.py`](02_intermediario/contrato.py) | enums e modelos do básico (01–03), para o intermediário importar |
| [`03_avancado/contrato.py`](03_avancado/contrato.py) | o mesmo + `Ferramenta` (04) e `Intencao` (06) |
| [`03_avancado/llm_simulado.py`](03_avancado/llm_simulado.py) | cliente simulado no formato da OpenAI |
| [`03_avancado/mercado.py`](03_avancado/mercado.py) | peças de 07–09 reunidas para o pipeline do 10 |

## Pydantic × dataclass × enum, nesta trilha

- **Pydantic na fronteira:** tudo que entra ou sai do modelo (resposta, argumentos de ferramenta, classificação), o pedido do
  usuário e a configuração do ambiente. Validação a cada criação, com mensagens que voltam para o modelo no retry.
- **dataclass no estado interno:** configuração congelada, contexto do pedido, histórico, uso, resultados. Quem cria é o seu
  código; validar a cada mudança seria custo sem ganho (e a pegadinha 5 do 09 mostra o limite disso).
- **enum para vocabulário fechado:** unidades, categorias, intenções, ferramentas, perfis, decisões. No schema, o enum vira lista
  de opções para o modelo; no código, `match` + teste de cobertura.
- **Código, não prompt, para o que precisa ser garantido:** permissões, orçamento, limites. O prompt informa o modelo; o código decide.

## Versão anterior

[`casos_originais/`](casos_originais/README.md): os cinco notebooks anteriores, mais densos e sem a progressão. Ficaram como
referência (cobrem alguns tópicos que a trilha não repete, como streaming parcial e FastAPI).
