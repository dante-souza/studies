# Seção 12 — Aplicações: teoria

> Notebooks: [`02`](02_consumindo_uma_api_rest.ipynb) consumindo uma API REST · [`03`](03_ingerindo_um_csv.ipynb) ingerindo um CSV ·
> [`04`](04_validando_argumentos_de_funcoes.ipynb) validando argumentos de funções · [`05`](05_geradores_de_codigo_de_modelos.ipynb)
> geradores de código de modelos. Dados: `pop_estimates.csv`, `csv_data.csv`, `rectangle_data.json`, `schema_1/2/3.json`,
> `geojs_samples.json` (respostas gravadas da API, para rodar offline).

## Onde o Pydantic entra numa aplicação

```
  API REST (JSON) ──► model_validate(response.json())   ─┐
  CSV (tudo string) ─► BeforeValidator + DictReader     ─┼──► objetos tipados ──► lógica
  chamada de função ─► @validate_call                   ─┘
  JSON Schema / dados de exemplo ─► datamodel-codegen ──► código de modelos (ponto de partida)
```

| caso | ferramenta | lição |
|---|---|---|
| API sem schema | modelo com `extra="ignore"`; obrigatório só o que o programa **precisa**, resto anulável | validador *after* em campo anulável **precisa tratar `None`** |
| CSV | `csv.DictReader` → `model_validate(row)`; `BeforeValidator` para `" 284,796,887 "` | registre a **linha** do erro e siga em frente |
| argumentos | `@validate_call` (e `validate_return=True`) | a exceção é levantada **para quem chama**; erro de retorno tem `loc=()` |
| geração de código | `datamodel-codegen` | bom para JSON Schema simples; não entende condicionais (`if/then/else`), não infere tipos de CSV, `pattern` vem sem âncora |

## Divergências encontradas na revisão

- API: `set_unknown_to_none` chama `.casefold()` em `None` (`AttributeError` cru); `raise_for_status` sem parênteses; falta `timeout=`.
- CSV: mensagem "could be parsed" sem o **not**; abrir com `newline=""`.
- `validate_call`: a versão "Python puro" anota `datetime | str` mas quebra com `datetime`.
- Geradores: duas células de código continham prosa; `pattern` `\d{5}` aceita `"abc12345xyz"`; `--reuse-model` reduz a duplicação que
  o curso faz à mão; o schema 3 não exige `membershipNumber` (o modelo do curso exige — decisão mais restritiva que o schema).
- Rede: a geojs.io não estava acessível no ambiente da reexecução; o notebook usa as respostas gravadas no notebook original (2024)
  como fallback e diz qual fonte usou.
