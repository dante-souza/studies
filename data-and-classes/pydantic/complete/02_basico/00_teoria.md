# Seção 2 — Básico: teoria

> Notebooks: [`02`](02_criando_um_modelo.ipynb) criando um modelo · [`03`](03_desserializacao.ipynb) desserialização ·
> [`04`](04_serializacao.ipynb) serialização · [`05`](05_coercao_de_tipos.ipynb) coerção · [`06`](06_campos_obrigatorios_e_opcionais.ipynb)
> obrigatórios × opcionais · [`07`](07_campos_anulaveis.ipynb) anuláveis · [`08`](08_combinando_anulavel_e_opcional.ipynb) anulável + opcional ·
> [`09`](09_inspecionando_campos.ipynb) inspecionando campos · [`10`](10_geracao_de_json_schema.ipynb) JSON Schema ·
> projeto: [`11`](11_projeto.ipynb) · [`12`](12_projeto_solucao_instrutor.ipynb) · [`13`](13_projeto_solucao_comentada.ipynb)
> ⚠️ Pegadinhas, efeitos colaterais e caveats da seção: [`99_pegadinhas_e_caveats`](99_pegadinhas_e_caveats.ipynb)

## Ideia central

Um modelo Pydantic é uma classe cujas **anotações de tipo viram contrato em tempo de execução**. Tudo o que entra passa pelo
validador; tudo o que sai passa pelo serializador.

```
          desserializar (validar)                        serializar
 dict  ──► Model.model_validate(d)      ──►  instância  ──► .model_dump()       ──► dict
 JSON  ──► Model.model_validate_json(s) ──►  instância  ──► .model_dump_json()  ──► str JSON
 kwargs──► Model(**kwargs)              ──►  instância
```

## Conceitos

| conceito | o que é | detalhe que pega |
|---|---|---|
| desserialização | dados externos → instância validada | `model_validate_json` faz o parse do JSON no `pydantic-core` (Rust), sem `json.loads` |
| serialização | instância → `dict`/JSON | `model_dump` mantém objetos Python (`date`, `UUID`); `model_dump_json` converte para tipos JSON |
| coerção (*lax*) | o Pydantic converte entradas "razoáveis" (`"10"` → `10`) | é o modo padrão; o modo *strict* é visto na seção 3 |
| obrigatório × opcional | **opcional = tem default**; obrigatório = sem default | não tem nada a ver com aceitar `None` |
| anulável | o tipo aceita `None` (`int \| None`) | anulável **sem** default continua obrigatório (precisa vir, mesmo que `null`) |
| `model_fields` | metadados dos campos (`FieldInfo`) | acesse pela **classe**; pela instância está depreciado desde a 2.11 |
| JSON Schema | `Model.model_json_schema()` | gerado a partir das mesmas anotações; documenta o contrato |

### Opcional × anulável (a matriz)

| declaração | pode faltar? | aceita `null`? |
|---|---|---|
| `x: int` | não | não |
| `x: int = 0` | sim | não |
| `x: int \| None` | não | sim |
| `x: int \| None = None` | sim | sim |

## Divergências encontradas na revisão (curso gravado no 2.5)

- `instancia.model_fields` está depreciado (2.11+): use `Classe.model_fields`.
- O curso dizia que `model_dump_json` usa `json.dumps` por baixo; na v2 quem serializa é o `pydantic-core`.
- Exemplo "versão JSON" que chamava `model_dump` (dict) — corrigido para `model_dump_json`.
- `user_list = user_list or []` troca a lista vazia do chamador por outra — o padrão correto é `if user_list is None`.

## Projeto

Modelo `Automobile` com campos obrigatórios, opcionais e anuláveis. A solução comentada revisa a tentativa original: `str = None`
deveria ser `str | None = None` (sem `| None`, um `null` explícito é rejeitado).
