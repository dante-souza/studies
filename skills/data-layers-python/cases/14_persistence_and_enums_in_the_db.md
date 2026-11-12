# Case 14 — Persistence and enums in the database

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** writing and reading enums and models through an ORM.
**Design:** store the enum **value** (a stable contract), read with `from_attributes=True`.

```python
status: Mapped[Status] = mapped_column(
    SAEnum(Status, native_enum=False, values_callable=lambda e: [m.value for m in e]))
```

**Pitfalls**
- By default, SQLAlchemy's `Enum` stores the member **name** (`'PAID'`), not the value (`'paid'`) **(V)**: renaming the member breaks old data; `values_callable` stores the value **(V)**.
- `use_enum_values=True` in Pydantic stores the **value** (`str`), not the member **(V)**: `is Status.PAID`, `isinstance(x, Status)` and `.name` stop working; with `StrEnum`, `==` is still `True` and hides the difference **(V)**.
- An enum that gains a member needs a migration when the database uses a native enum type.

**Possibilities**
- A `CHECK` constraint generated from the enum's list of values.
- A reference table when the vocabulary changes often (enum only for what is stable).
