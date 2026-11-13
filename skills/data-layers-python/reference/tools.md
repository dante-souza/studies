# Quick reference: Enum, Pydantic and dataclass

[← SKILL.md](../SKILL.md)

## Enum

| Type | When | Note |
|---|---|---|
| `StrEnum` | text values that go to JSON, prompts, the database | the member **is** a `str`: compares equal to text, shows as text in f-strings |
| `IntEnum` | legacy numeric codes | compares equal to `int` (may hide type errors) |
| `Enum` | pure identity, no equality with primitives | `Enum("x") == "x"` is `False` |
| `Flag` | combinable permissions and capabilities | `A \| B`, `in`; beware of `Flag(0)` |
| `Literal[...]` | local vocabulary of a single model | no behavior, no reuse; use an enum when the vocabulary travels |

## Pydantic (v2)

| Feature | Use |
|---|---|
| `ConfigDict(extra="forbid")` | untrusted input: an unknown key is an error |
| `ConfigDict(frozen=True)` | immutable and hashable model (if the fields are) |
| `ConfigDict(strict=True)` / `Strict()` | no conversion (`"1"` does not become `1`) |
| `ConfigDict(validate_default=True)` | defaults are validated too |
| `ConfigDict(from_attributes=True)` | read objects (ORM) by attribute |
| `ConfigDict(validate_by_name=True)` | accept the field name as well as the alias |
| `Field(gt=, le=, pattern=, description=)` | constraints; `description` goes to the JSON Schema |
| `BeforeValidator` / `AfterValidator` | normalize before / rule after the type |
| `model_validator(mode="after")` | cross-field rule; receives `ValidationInfo` (context) |
| `PrivateAttr` | computed value stored on the object, outside the schema |
| `TypeAdapter(T)` | validate types that are not models (`list[Item]`, dataclass) |
| `BaseSettings` | configuration from env and `.env`, with `SecretStr` |
| `model_dump(mode="json")` | JSON-safe dict (Decimal, date, enum as value) |
| `model_json_schema()` | contract for documentation and for LLM prompts |

Execution order: `BeforeValidator` (several: **reverse** order) → type and `Field` constraints → `AfterValidator` →
`model_validator(mode="after")`.

## dataclass

| Feature | Use |
|---|---|
| `frozen=True` | immutable and hashable; shallow |
| `slots=True` | less memory, fixed attributes; recreates the class |
| `kw_only=True` | keyword-only constructor (avoids swapped positions) |
| `field(default_factory=...)` | mutable default |
| `__post_init__` | core **invariants**, not input validation |
| `dataclasses.replace(obj, x=...)` | modified copy of a frozen object |
| `asdict` | recursive export (copies everything; expensive on large objects) |
