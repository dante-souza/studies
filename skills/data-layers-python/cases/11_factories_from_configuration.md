# Case 11 — Factories from configuration

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** the config says which implementation to use (sources, exporters, strategies).
**Design:** a discriminated union on a `Literal` for the parameters; a `dict[Enum, type]` registry for the implementation.

```python
class CsvSource(BaseModel):
    kind: Literal["csv"]
    path: Path

class ApiSource(BaseModel):
    kind: Literal["api"]
    url: HttpUrl

Source = Annotated[CsvSource | ApiSource, Field(discriminator="kind")]

class Pipeline(BaseModel):
    sources: list[Source]

READERS: dict[str, type[Reader]] = {"csv": CsvReader, "api": ApiReader}
assert set(READERS) == {"csv", "api"}
```

**Pitfalls**
- A union without a discriminator tries the members and produces confusing errors; with a discriminator, the error points to the right type.
- Registration through `__init_subclass__(..., key=...)` + `@dataclass(slots=True)`: the class is recreated and the hook runs again without the kwargs (`TypeError`) **(V)**; use a `ClassVar` for the key.
- `frozen=True` on a root model with non-frozen submodels: the root is not hashable **(V)**.

**Possibilities**
- Abstract factory: an "environment profile" enum picks a coherent set of implementations.
- Plugins: the registry accepts new keys, with a test that the enum and the registry move together.
