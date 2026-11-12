# Caso 06 — Contrato com contexto

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** a mesma resposta é válida para um pedido e inválida para outro (orçamento, despensa, preços do dia).
**Desenho:** contexto `frozen` passado em `context=`; `model_validator` lê e falha sem contexto; valor calculado em `PrivateAttr`.

```python
@dataclass(frozen=True)
class ContextoPedido:
    orcamento: Decimal
    precos: Mapping[str, tuple[Decimal, Unidade]]
    despensa: Mapping[str, tuple[Decimal, Unidade]] = field(default_factory=dict)

    def __post_init__(self):
        for nome in ("precos", "despensa"):
            object.__setattr__(self, nome, MappingProxyType(dict(getattr(self, nome))))

class ListaComContexto(ListaDeCompras):
    _custo: Decimal | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def regras_com_contexto(self, info: ValidationInfo):
        ctx = info.context
        if not isinstance(ctx, ContextoPedido):
            raise ValueError("contexto obrigatório: valide com context=ContextoPedido(...)")
        total = ...                                   # converte unidades, desconta despensa, Decimal
        if total > ctx.orcamento:
            raise ValueError(f"custo R$ {total} passa do orçamento de R$ {ctx.orcamento}")
        self._custo = total
        return self

lista = ListaComContexto.model_validate_json(texto, context=ctx)
```

**Pegadinhas**
- O JSON Schema de `ListaComContexto` é idêntico ao de `ListaDeCompras`: o modelo não vê as regras; diga-as no prompt **(V)**.
- O construtor não recebe contexto (sempre falha); `model_copy(update=...)` não valida e carrega o custo velho **(V)**.
- `frozen=True` não congela o dict interno; `MappingProxyType` sim **(V)**.
- `Decimal(0.1)` carrega o erro do float; use `Decimal(str(x))` **(V)**.

**Possibilidades**
- O mesmo contrato com contextos diferentes nos testes (orçamento folgado e apertado).
- Contexto com relógio injetado (datas de validade) e perfil do usuário.
