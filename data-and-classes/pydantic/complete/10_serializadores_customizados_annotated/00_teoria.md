# Seção 10 — Serializadores customizados com `Annotated`: teoria

> Notebooks: [`02`](02_serializadores_customizados.ipynb) serializadores customizados · projeto: [`03`](03_projeto.ipynb) ·
> [`04`](04_projeto_solucao_instrutor.ipynb) · [`05`](05_projeto_solucao_comentada.ipynb)
> ⚠️ Pegadinhas, efeitos colaterais e caveats da seção: [`99_pegadinhas_e_caveats`](99_pegadinhas_e_caveats.ipynb)

## Ideia central

Assim como validadores podem morar no **tipo** (seção 8), serializadores também. Um tipo `Annotated` passa a carregar o ciclo completo
de um dado de domínio:

```python
DateTimeUTC = Annotated[
    datetime,
    BeforeValidator(parse_datetime),                       # entrada: aceita "1/1/2020 3pm"
    AfterValidator(make_utc),                              # normaliza: sempre aware em UTC
    PlainSerializer(dt_json_serializer, when_used="json-unless-none"),   # saída JSON: formato próprio
]
```

```
 entrada ─► Before ─► tipo ─► After ─► valor ─► PlainSerializer ─► saída
                                                (só quando when_used permitir)
```

| peça | papel |
|---|---|
| `PlainSerializer(f)` | **substitui** a serialização padrão |
| `WrapSerializer(f)` | recebe o `handler` padrão; pós-processa em vez de substituir |
| `when_used` | `"always"`, `"unless-none"`, `"json"`, `"json-unless-none"` |
| `return_type` / anotação `-> str` | define o tipo no JSON Schema de serialização |
| `@field_serializer` | a mesma coisa, mas presa a campos de um modelo |

## Simetria (lição do projeto)

Um tipo que **escreve** `2023/06/01` também precisa **ler** `2023/06/01`; senão o JSON que o próprio modelo gera não volta para o
modelo (o Pydantic só aceita datas ISO). A solução do instrutor tem esse problema; a comentada acrescenta um `BeforeValidator` que aceita
o formato de saída e dá erro claro para datas impossíveis (`2023/13/01`).

## Divergências encontradas na revisão

- O requisito pede `(UTC)` entre parênteses, mas o formato do curso gera `UTC` sem parênteses.
- `pytz` pode ser trocado por `datetime.timezone.utc`.
- Texto que dizia "desserialização" num teste de serialização.
