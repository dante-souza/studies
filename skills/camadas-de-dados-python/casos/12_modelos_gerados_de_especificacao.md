# Caso 12 — Modelos gerados de especificação

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** um meta-modelo (YAML) descreve entidades; gerar enums, modelos e até código-fonte.
**Desenho:** validar a especificação com Pydantic → `Enum("Nome", valores)` → `create_model` / `make_dataclass` →
opcionalmente gerar `.py` e checar com mypy.

```python
Modelo = create_model(
    spec.nome,
    __config__=ConfigDict(extra="forbid"),
    **{c.nome: (tipo_de(c), Field(**c.restricoes)) for c in spec.campos},
)
```

Separe **normalização** (`BeforeValidator`, roda antes das restrições) de **validação** (`AfterValidator`).

**Pegadinhas**
- `AfterValidator(upper)` depois de `pattern` em maiúsculas: o padrão vê o texto ainda minúsculo e falha **(V)**; normalize com `BeforeValidator`.
- `StringConstraints(pattern=...)` roda antes de `to_lower` **(V)**.
- Default de enum vindo da spec não é convertido: converta ao montar o modelo **(V)**.
- `Field` antes de `BeforeValidator` mantém a mensagem específica do campo **(V)**.
- Código gerado: docstring vinda da spec pode injetar código (use `repr`) **(V)**; `repr(date)` não é literal Python válido sem import **(V)**.
- Colisões: aliases repetidos, nomes que sombreiam atributos do `BaseModel`, valores diferentes que viram o mesmo nome de membro **(V)**.
- `uuid4` usado como **tipo** (é função): o tipo é `UUID`, com `default_factory=uuid4` **(V)**.

**Possibilidades**
- `make_dataclass` para o núcleo e `create_model` para a borda, a partir da mesma spec.
- Gerar código para versionar e revisar em diff, em vez de criar classes só em tempo de execução.
