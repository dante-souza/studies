# Seção 4 — Aliases, serialização e desserialização: teoria

> Notebooks: [`02`](02_aliases_e_valores_default.ipynb) aliases e defaults · [`03`](03_funcoes_geradoras_de_alias.ipynb) geradores de alias ·
> [`04`](04_desserializando_por_nome_ou_alias.ipynb) por nome ou alias · [`05`](05_aliases_de_serializacao.ipynb) aliases de serialização ·
> [`06`](06_aliases_de_validacao.ipynb) aliases de validação · [`07`](07_serializadores_customizados.ipynb) serializadores customizados ·
> projeto: [`08`](08_projeto.ipynb) · [`09`](09_projeto_solucao_instrutor.ipynb) · [`10`](10_projeto_solucao_comentada.ipynb)
> ⚠️ Pegadinhas, efeitos colaterais e caveats da seção: [`99_pegadinhas_e_caveats`](99_pegadinhas_e_caveats.ipynb)

## Ideia central

O **nome Python** do campo e o **nome no mundo externo** são coisas diferentes. Aliases fazem a ponte — e podem ser diferentes na
entrada (validação) e na saída (serialização).

```
   entrada                       modelo                        saída
 "completionDate" ─validation_alias─► manufactured_date ─serialization_alias─► "manufacturedDate"
 "firstName"      ─────── alias (os dois sentidos) ───► first_name ──────────► "firstName" (by_alias=True)
```

| ferramenta | sentido | uso típico |
|---|---|---|
| `Field(alias=...)` | entrada e saída | API externa usa outro nome |
| `validation_alias` | só entrada | renomear um campo vindo de um fornecedor |
| `serialization_alias` | só saída | expor um nome diferente do interno |
| `AliasChoices("a", "b")` | entrada | aceitar vários nomes; vence o **primeiro da lista** que existir nos dados |
| `AliasPath("a", 0, "b")` | entrada | buscar um valor aninhado (complemento: não aparece no curso) |
| `alias_generator` / `AliasGenerator` | ambos | regra global (`to_camel`, `to_pascal`); `AliasGenerator` aceita funções diferentes para validação e serialização |
| `validate_by_name` / `validate_by_alias` | entrada | aceitar o nome Python além do alias (sucessores de `populate_by_name`) |
| `serialize_by_alias` | saída | serializar por alias sem passar `by_alias=True` em cada dump |
| `@field_serializer(..., when_used=...)` | saída | formato próprio (ex.: data `YYYY/MM/DD`) só em JSON, só se não-`None` etc. |

## Ida e volta (*round-trip*)

Se a saída usa um nome que a entrada não aceita, o JSON produzido pelo modelo **não volta** para o modelo. A solução comentada resolve com
`AliasChoices(nome_de_entrada, nome_de_saída)` — o mesmo problema reaparece nas seções 10 e 11 e é tratado lá.

## Divergências encontradas na revisão

- `AliasChoices`: o curso dizia que vence o valor "mais recente" nos dados; na verdade vence a **ordem dentro do `AliasChoices`**.
- `AliasGenerator` hoje suporta aliases de serialização (o curso dizia que não).
- `populate_by_name` → `validate_by_name` + `validate_by_alias` (2.11+).
- `pytz` pode ser substituído por `datetime.timezone` / `zoneinfo` da biblioteca padrão.
- Trechos que diziam "desserializar" num exemplo de serialização; texto em célula de código.

## Projeto

A solução comentada adota a ideia da tentativa original (`make_alias` = camelCase + `removesuffix("_")`), mas aponta que no `.py`
original `completionDate`/`doors` estavam em `alias=` (os dois sentidos), o que faz os testes `by_alias` **falharem**, e que faltava o
serializador de datas.
