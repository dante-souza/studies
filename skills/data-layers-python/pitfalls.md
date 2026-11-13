# Pitfall catalog

[← SKILL.md](SKILL.md)

Marks: **(V)** verified in the study, with executed code; **(R)** observed in a real LLM response; no mark = known library
behavior, not tested in the study. Each pitfall is detailed in the matching use case ([`cases/`](cases/)).

| Area | Pitfall | Remedy |
|---|---|---|
| Pydantic | `description` is not a rule **(V)** | enum, constraint, validator |
| Pydantic | validators do not show up in the JSON Schema **(V)** | state the rule in the prompt/documentation too |
| Pydantic | native strict mode: optional becomes required-nullable **(V)** | expect an explicit `null` |
| Pydantic | `model_copy(update=)` does not validate **(V)** | revalidate |
| Pydantic | defaults are not validated **(V)** | `validate_default=True` or convert the default |
| Pydantic | several `BeforeValidator`s: reverse order **(V)** | one composed validator, or a deliberate order |
| Pydantic | constraints run before `AfterValidator` **(V)** | normalize with `BeforeValidator` |
| Pydantic | `info.data` lacks the field that failed (KeyError) **(V)** | `info.data.get(...)` |
| Pydantic | `exclude` silently ignores aliases **(V)** | use field names |
| Pydantic | `model_validate(instance)` returns the same instance **(V)** | `model_copy(deep=True)` if you need a copy |
| Pydantic | `str(SecretStr)` is the mask **(V)** | `get_secret_value()` only where used |
| Pydantic | `validation_alias` + `extra="ignore"` swallows the field name **(V)** | `validate_by_name=True` |
| Pydantic | 2.13.5: `_missing_` receives `None` from JSON **(V)** | `BeforeValidator` for open enums |
| Pydantic | `use_enum_values` stores `str`; `==` still works with StrEnum **(V)** | avoid it, or do not rely on `is`/`isinstance` |
| Pydantic | error order changes between versions **(V)** | test content |
| Pydantic + dataclass | `TypeAdapter` ignores extra keys **(V)** | `__pydantic_config__ = {"extra": "forbid"}` |
| dataclass | does not validate **(V)** | Pydantic at the border |
| dataclass | mutable default **(V)** | `default_factory` |
| dataclass | frozen is shallow **(V)** | `MappingProxyType`, tuples |
| dataclass | `slots=True` + `__init_subclass__` kwargs **(V)** | `ClassVar` |
| Enum | exact comparison **(V)** | normalize at the border |
| Enum | `match` without `case _` **(V)** | `case _: raise` or `assert_never` |
| Enum | table without coverage **(V)** | `assert not set(E) - T.keys()` |
| Enum | renaming a value **(V)** | the value is a contract; rename only the name |
| Enum | `Flag(0) in X` **(V)** | explicit `is None` |
| Enum + ORM | SQLAlchemy stores the name by default **(V)** | `values_callable` |
| YAML | `no`/`off` → `False`, `3.10` → `3.1` **(V)** | quotes, `safe_load` |
| Numbers | float for money **(V)** | `Decimal(str(x))` |
| Numbers | `"1.5"` → `15` in a Brazilian-format parser **(V)** | strict regex |
| LLM | JSON wrapped in a fence/text **(R)** | border type `llm_output(Model)` |
| LLM | slicing `{`…`}` breaks on braces in prose and turns a bare list into a `dict` with no error **(V)** | decode with `raw_decode` |
| LLM | `json.loads` + `model_validate` with `strict=True` rejects `date`/`Decimal` **(V)** | validate in JSON mode (`Json[...]`) |
| LLM | two JSONs in the response: the first one wins **(V)** | a single JSON in the prompt; validation rejects the example |
| LLM | non-numeric quantity **(R)** | decide in the contract |
| LLM | uncalibrated confidence **(R)** | evaluation with expected answers |
| LLM | name does not match the key **(R)** | canonical keys, synonyms |
| LLM | cutting history breaks tool pairs **(V)** | cut by turn |
| Python | `assert` disappears with `-O` **(V)** | `if ...: raise` for rules |
| Python | the `except ... as ex` variable is deleted when the block ends **(V)** | copy what you need inside the block |
| Python 3.11 | backslash inside an f-string expression **(V)** | helper variable |
| Notebook | two classes with the same name confuse `pickle` **(V)** | distinct names per cell |
