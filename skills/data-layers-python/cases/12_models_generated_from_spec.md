# Case 12 — Models generated from a spec

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** a meta-model (YAML) describes entities; generate enums, models and even source code.
**Design:** validate the spec with Pydantic → `Enum("Name", values)` → `create_model` / `make_dataclass` → optionally
generate a `.py` and check it with mypy.

```python
Model = create_model(
    spec.name,
    __config__=ConfigDict(extra="forbid"),
    **{f.name: (type_of(f), Field(**f.constraints)) for f in spec.fields},
)
```

Separate **normalization** (`BeforeValidator`, runs before the constraints) from **validation** (`AfterValidator`).

**Pitfalls**
- `AfterValidator(upper)` after an uppercase `pattern`: the pattern still sees lowercase text and fails **(V)**; normalize with a `BeforeValidator`.
- `StringConstraints(pattern=...)` runs before `to_lower` **(V)**.
- An enum default coming from the spec is not converted: convert it when building the model **(V)**.
- `Field` before `BeforeValidator` keeps the field-specific message **(V)**.
- Generated code: a docstring from the spec can inject code (use `repr`) **(V)**; `repr(date)` is not a valid Python literal without an import **(V)**.
- Collisions: repeated aliases, names that shadow `BaseModel` attributes, different values that turn into the same member name **(V)**.
- `uuid4` used as a **type** (it is a function): the type is `UUID`, with `default_factory=uuid4` **(V)**.

**Possibilities**
- `make_dataclass` for the core and `create_model` for the border, from the same spec.
- Generate code to version and review in diffs, instead of creating classes only at runtime.
