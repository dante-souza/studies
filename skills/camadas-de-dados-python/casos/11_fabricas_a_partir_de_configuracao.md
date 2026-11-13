# Caso 11 — Fábricas a partir de configuração

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** a config diz qual implementação usar (fontes, exportadores, estratégias).
**Desenho:** união discriminada por `Literal` para os parâmetros; registro `dict[Enum, type]` para a implementação.

```python
class FonteCSV(BaseModel):
    tipo: Literal["csv"]
    caminho: Path

class FonteAPI(BaseModel):
    tipo: Literal["api"]
    url: HttpUrl

Fonte = Annotated[FonteCSV | FonteAPI, Field(discriminator="tipo")]

class Pipeline(BaseModel):
    fontes: list[Fonte]

LEITORES: dict[str, type[Leitor]] = {"csv": LeitorCSV, "api": LeitorAPI}
assert set(LEITORES) == {"csv", "api"}
```

**Pegadinhas**
- União sem discriminador tenta os membros e produz erros confusos; com discriminador, o erro aponta o tipo certo.
- Registro por `__init_subclass__(..., chave=...)` + `@dataclass(slots=True)`: a classe é recriada e o hook roda de novo sem os kwargs (`TypeError`) **(V)**; use `ClassVar` para a chave.
- `frozen=True` em modelo raiz com submodelos não-frozen: o raiz não é hashable **(V)**.

**Possibilidades**
- Abstract factory: um enum de "perfil de ambiente" escolhe um conjunto coerente de implementações.
- Plugins: o registro aceita novas chaves, com teste de que o enum e o registro andam juntos.
