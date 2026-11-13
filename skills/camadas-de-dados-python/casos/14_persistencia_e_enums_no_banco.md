# Caso 14 — Persistência e enums no banco

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** gravar e ler enums e modelos via ORM.
**Desenho:** gravar o **valor** do enum (contrato estável), ler com `from_attributes=True`.

```python
status: Mapped[Status] = mapped_column(
    SAEnum(Status, native_enum=False, values_callable=lambda e: [m.value for m in e]))
```

**Pegadinhas**
- Por padrão, o `Enum` do SQLAlchemy grava o **nome** do membro (`'PAGO'`), não o valor (`'pago'`) **(V)**: renomear o membro quebra dados antigos; `values_callable` grava o valor **(V)**.
- `use_enum_values=True` no Pydantic guarda o **valor** (`str`), não o membro **(V)**: `is Status.PAGO`, `isinstance(x, Status)` e `.name` deixam de funcionar; com `StrEnum`, o `==` continua `True` e esconde a diferença **(V)**.
- Enum que ganha membro precisa de migração quando o banco usa tipo enum nativo.

**Possibilidades**
- `CHECK` constraint gerado da lista de valores do enum.
- Tabela de referência quando o vocabulário muda com frequência (enum só para o que é estável).
