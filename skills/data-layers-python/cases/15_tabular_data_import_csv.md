# Case 15 — Tabular data import (CSV)

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** a spreadsheet with Brazilian-format numbers (`1.234,56`), dates, categories.
**Design:** one model per row; validate row by row to collect errors with the row number; create a `TypeAdapter` once.

```python
def parse_br_number(v):
    if isinstance(v, str):
        text = v.strip()
        if not re.fullmatch(r"-?\d{1,3}(\.\d{3})*(,\d+)?|-?\d+(,\d+)?", text):
            raise ValueError(f"invalid number format: {v!r}")
        return Decimal(text.replace(".", "").replace(",", "."))
    return v

BrAmount = Annotated[Decimal, BeforeValidator(parse_br_number)]

class Sale(BaseModel):
    date: date
    product: str
    amount: BrAmount

valid, errors = [], []
for number, row in enumerate(csv.DictReader(file), start=2):
    try:
        valid.append(Sale.model_validate(row))
    except ValidationError as ex:
        errors.append((number, ex.errors(include_url=False)))
```

`parse_br_number` tested: accepts `1.234,56` → `1234.56`, `1234,5`, `-2,50`; rejects `1.5`, `12.34` and `1,234.56` **(V)**.

**Pitfalls**
- `"1.5"` read as `15` by a parser that only strips dots **(V)**: require the format with a strict regex.
- `dd/mm/yyyy` dates are not ISO: convert with `strptime` in a `BeforeValidator`, with a clear message **(V)**.
- In 2.14, the JSON Schema of `Decimal` lost its `pattern` **(V)**: do not depend on it.

**Possibilities**
- An error report per row (table) before importing; "all or nothing" vs "import the valid ones".
- `TypeAdapter(list[Sale])` when the whole file must be valid.
