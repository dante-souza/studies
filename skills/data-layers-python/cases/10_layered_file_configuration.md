# Case 10 — Layered file configuration

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** `base.yaml` + `prod.yaml` + environment variables, with secrets.
**Design:** load each source, merge in layers, validate **once** with Pydantic; secrets only from the environment.

| Format | Native types | Watch out |
|---|---|---|
| JSON | number, bool, null, list, object | no comments |
| TOML | includes dates and distinct ints/floats | `tomllib` only reads |
| YAML | everything, implicitly | YAML 1.1 (PyYAML): `no`/`off` become `False`, `3.10` becomes `3.1`; quoted `"3.10"` stays text **(V)**; use `safe_load` |
| INI | text only | every conversion is yours (or Pydantic's) |
| `.env` | text only | quotes and spaces vary between libraries |

```python
def merge_layers(base: dict, extra: dict) -> dict:
    result = dict(base)
    for key, value in extra.items():
        if value is None and isinstance(base.get(key), dict):
            raise ValueError(f"'{key}: null' would erase the whole section")
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            result[key] = merge_layers(base[key], value)
        else:
            result[key] = value
    return result

config = TypeAdapter(AppConfig).validate_python(merge_layers(base, prod))
```

**Pitfalls**
- A naive `deep_merge`: `section: null` in the production file erases the whole section **(V)**.
- A dataclass through `TypeAdapter` ignores extra keys (typos vanish): `__pydantic_config__ = {"extra": "forbid"}` **(V)**, which propagates to nested dataclasses; `TypeAdapter(config=...)` is refused for dataclasses **(V)**.
- `strict=True` with a nested dataclass requires the exact instance (BaseModel accepts a dict) **(V)**.
- Defaults are not validated: an enum default written as `2` stays an `int` **(V)**.

**Possibilities**
- Explicit precedence: arguments > environment > `.env` > file > default (`BaseSettings` already follows most of it).
- Policies and presets in files (`ConfigDict` from YAML, validated before being applied).
