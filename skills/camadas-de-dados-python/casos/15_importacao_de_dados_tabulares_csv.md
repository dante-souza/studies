# Caso 15 — Importação de dados tabulares (CSV)

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** planilha com números no formato brasileiro, datas, categorias.
**Desenho:** um modelo por linha; validar linha a linha para coletar erros com número da linha; `TypeAdapter` criado uma vez.

```python
def parse_brl(v):
    if isinstance(v, str):
        texto = v.strip()
        if not re.fullmatch(r"-?\d{1,3}(\.\d{3})*(,\d+)?|-?\d+(,\d+)?", texto):
            raise ValueError(f"número em formato inválido: {v!r}")
        return Decimal(texto.replace(".", "").replace(",", "."))
    return v

ValorBRL = Annotated[Decimal, BeforeValidator(parse_brl)]

class Venda(BaseModel):
    data: date
    produto: str
    valor: ValorBRL

validos, erros = [], []
for numero, linha in enumerate(csv.DictReader(arquivo), start=2):
    try:
        validos.append(Venda.model_validate(linha))
    except ValidationError as ex:
        erros.append((numero, ex.errors(include_url=False)))
```

`parse_brl` testado: aceita `1.234,56` → `1234.56`, `1234,5`, `-2,50`; rejeita `1.5`, `12.34` e `1,234.56` **(V)**.

**Pegadinhas**
- `"1.5"` lido como `15` por um parser que só remove pontos **(V)**: exija o formato com regex estrita.
- Datas `dd/mm/aaaa` não são ISO: converta com `strptime` num `BeforeValidator`, com mensagem clara **(V)**.
- No 2.14, o JSON Schema de `Decimal` perdeu o `pattern` **(V)**: não dependa dele.

**Possibilidades**
- Relatório de erros por linha (tabela) antes de importar; modo "tudo ou nada" x "importa os válidos".
- `TypeAdapter(list[Venda])` quando o arquivo precisa ser válido inteiro.
