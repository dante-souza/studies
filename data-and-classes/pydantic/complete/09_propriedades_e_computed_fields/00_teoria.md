# Seção 9 — Propriedades e campos calculados: teoria

> Notebooks: [`02`](02_propriedades.ipynb) propriedades · [`03`](03_computed_fields.ipynb) computed fields · projeto: [`04`](04_projeto.ipynb) ·
> [`05`](05_projeto_solucao_instrutor.ipynb) · [`06`](06_projeto_solucao_comentada.ipynb)
> ⚠️ Pegadinhas, efeitos colaterais e caveats da seção: [`99_pegadinhas_e_caveats`](99_pegadinhas_e_caveats.ipynb)

## Ideia central

Nem todo dado precisa ser **armazenado**: alguns são **derivados** de outros campos. A pergunta é se o valor derivado deve sair na
serialização.

| recurso | serializado? | no JSON Schema? | quando usar |
|---|---|---|---|
| `@property` | não | não | conveniência interna (`circle.area`) |
| `@cached_property` | não | não | cálculo caro, origem **imutável** |
| `@computed_field` + `@property` | **sim** | sim (modo `serialization`) | o consumidor precisa do valor derivado |
| `@computed_field` + `@cached_property` | sim | sim | idem, e o cálculo é caro |

```
campos armazenados ──► model_dump()  ──► { ...campos..., ...campos calculados (sempre por último) }
        │                                        ▲
        └──── @computed_field (calculado na hora) ┘
```

Regras: o campo calculado **precisa** de anotação de retorno (sem ela, `PydanticUserError` na definição da classe); entra em
`model_dump`/`model_dump_json`, respeita `alias_generator`/`alias`, aceita `repr=False`; **não** é aceito na entrada — com
`extra="forbid"`, mandar o valor calculado de volta é erro (ver seções 10 e 11).

## Cache × mutabilidade (o bug clássico)

```
car.registration_country_code   # calcula 'USA' e guarda no __dict__ (cached_property)
car.registration_country = "fr" # validate_assignment grava 'France'...
car.registration_country_code   # ...mas o cache continua 'USA'  ✗
```

Três saídas: (1) não cachear; (2) **congelar** a origem (`frozen=True`); (3) invalidar o cache ao atribuir (sobrescrever `__setattr__`
e remover a chave do `__dict__`). A solução comentada desta seção usa (3) e mede o efeito com um contador de "consultas ao banco"; a da
seção 11 usa (2), que fica mais simples depois da composição.

## Divergências encontradas na revisão

- Solução do instrutor: `country_code_lookup[self.registration_country]` com país `None` → `KeyError` em **todo** `model_dump()`;
  o tipo de retorno deveria ser `str | None`.
- Solução do instrutor: código de país cacheado fica desatualizado depois de trocar o país.
