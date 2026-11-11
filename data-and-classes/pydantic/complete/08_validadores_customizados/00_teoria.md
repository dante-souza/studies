# Seção 8 — Validadores customizados: teoria

> Notebooks: [`01`](01_introducao.ipynb) introdução (slides) · [`02`](02_validadores_after.ipynb) *after* · [`03`](03_validadores_before.ipynb)
> *before* · [`04`](04_validadores_before_e_after.ipynb) *before* + *after* · [`05`](05_validadores_com_annotated.ipynb) com `Annotated` ·
> [`06`](06_validacoes_dependentes_de_campos.ipynb) dependentes de campos · projeto: [`07`](07_projeto.ipynb) ·
> [`08`](08_projeto_solucao_instrutor.ipynb) · [`09`](09_projeto_solucao_comentada.ipynb)

## Ideia central

Quando nenhum tipo ou restrição pronta resolve, escrevemos a regra. A pergunta é **quando** ela roda em relação à validação do tipo.

```
entrada ─► BeforeValidator(s) ─► validação do tipo (core) ─► AfterValidator(s) ─► valor final
           recebe o dado CRU         int, date, str...       recebe o valor JÁ tipado
           (normalizar, converter)                           (regras de negócio)
```

| forma | onde | quando usar |
|---|---|---|
| `@field_validator("campo", mode="after")` | no modelo | regra de um ou mais campos daquele modelo |
| `@field_validator(..., mode="before")` | no modelo | aceitar formatos que o tipo não aceita (ex.: `"1,234"` → `1234`) |
| `Annotated[T, AfterValidator(f)]` | no tipo | regra **reutilizável** em vários modelos (ex.: `Country`) |
| `info.data` (`ValidationInfo`) | dentro do validador | ler campos **já validados** — só os declarados **antes** |
| `@model_validator(mode="after")` | no modelo | regra entre vários campos com o objeto completo |

Validadores devem levantar `ValueError` (ou `AssertionError`); o Pydantic converte em `ValidationError` com a localização do campo.
Qualquer **outra** exceção (`TypeError`, `KeyError`) escapa crua — é o bug da solução do instrutor abaixo.

## Pegadinhas verificadas

- **Ordem importa:** `info.data` só tem os campos declarados antes do campo atual (e só os que passaram).
- **`validate_default=True` + validador que não trata `None`:** o default `None` também passa pelo validador. Na solução do instrutor,
  `data["manufactured_date"] > None` levanta `TypeError` para qualquer carro sem `registrationDate`.
- **`model_validator(mode="after")` em atribuição:** com `validate_assignment=True`, o erro é levantado, mas o valor **já foi gravado** —
  a instância fica inconsistente. Validadores de campo bidirecionais (cada data checa a outra via `info.data`) rejeitam **antes** de gravar.

## Projeto

Tipo `Country` (normaliza `"UK"`, `"uk "` → `United Kingdom`) e regra "registro não pode ser antes da fabricação". A solução comentada
inclui o Brasil, colapsa espaços internos, trata ausência/`None` e valida a regra nos dois campos, para a atribuição nunca deixar a
instância inconsistente.
