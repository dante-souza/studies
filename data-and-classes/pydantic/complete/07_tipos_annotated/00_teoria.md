# Seção 7 — Tipos `Annotated`: teoria

> Notebooks: [`02`](02_pydantic_e_tipos_annotated.ipynb) Pydantic e `Annotated` · [`03`](03_tipos_annotated_e_type_variables.ipynb)
> `Annotated` e `TypeVar` · [`04`](04_restricoes_de_string.ipynb) restrições de string · projeto: [`05`](05_projeto.ipynb) ·
> [`06`](06_projeto_solucao_instrutor.ipynb) · [`07`](07_projeto_solucao_comentada.ipynb)
> ⚠️ Pegadinhas, efeitos colaterais e caveats da seção: [`99_pegadinhas_e_caveats`](99_pegadinhas_e_caveats.ipynb)

## Ideia central

`Annotated[T, metadado...]` permite **dar nome a uma regra** e reaproveitá-la: o tipo continua sendo `T` para o Python e para o
editor; o Pydantic lê os metadados (`Field(...)`, validadores, serializadores).

```python
BoundedString = Annotated[str, Field(min_length=2, max_length=50)]
T = TypeVar("T")
BoundedList   = Annotated[list[T], Field(min_length=1, max_length=5)]

top_features: BoundedList[BoundedString] | None = None    # lista de 1–5 strings de 2–50 caracteres
```

```
Annotated[ tipo base , restrições/validadores/serializadores ]  ──►  "tipo de domínio" reutilizável
                          (seções 7, 8 e 10 vão empilhando metadados aqui)
```

| técnica | para quê |
|---|---|
| `Annotated[T, Field(...)]` | restrição reutilizável |
| `TypeVar` + `Annotated[list[T], ...]` | tipo **genérico** parametrizável (`BoundedList[int]`, `BoundedList[str]`) |
| `TypeAdapter(Tipo)` | validar/serializar um tipo **sem** criar modelo — ótimo para testar o tipo isoladamente |
| `StringConstraints` | restrições de string (strip, lower, pattern) num metadado só |

## Divergência encontrada na revisão

- Na solução do instrutor, `id_` voltou a ser `UUID4 | None` — regressão do requisito da seção 6 (um `"id": null` passa).

## Projeto

Criar `BoundedString` e `BoundedList[T]` e usar em `manufacturer`, `series_name`, `vin`, `registration_country`, `license_plate` e no novo
`top_features`. A solução comentada testa os tipos com `TypeAdapter` (sem modelos "de teste" de um campo) e mantém `id_` não anulável.
