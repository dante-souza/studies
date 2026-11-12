# Case 06 — Contract with context

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** the same response is valid for one request and invalid for another (budget, pantry, today's prices).
**Design:** a `frozen` context passed in `context=`; a `model_validator` reads it and fails without it; the computed value
lives in a `PrivateAttr`.

```python
@dataclass(frozen=True)
class OrderContext:
    budget: Decimal
    prices: Mapping[str, tuple[Decimal, Unit]]
    pantry: Mapping[str, tuple[Decimal, Unit]] = field(default_factory=dict)

    def __post_init__(self):
        for name in ("prices", "pantry"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

class ShoppingListInContext(ShoppingList):
    _cost: Decimal | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def context_rules(self, info: ValidationInfo):
        ctx = info.context
        if not isinstance(ctx, OrderContext):
            raise ValueError("context required: validate with context=OrderContext(...)")
        total = ...                                   # convert units, subtract pantry, Decimal
        if total > ctx.budget:
            raise ValueError(f"cost {total} exceeds the budget of {ctx.budget}")
        self._cost = total
        return self

shopping_list = ShoppingListInContext.model_validate_json(text, context=ctx)
```

**Pitfalls**
- The JSON Schema of `ShoppingListInContext` is identical to `ShoppingList`'s: the model does not see the rules; state them in the prompt **(V)**.
- The constructor cannot receive context (it always fails); `model_copy(update=...)` does not validate and keeps the stale cost **(V)**.
- `frozen=True` does not freeze the inner dict; `MappingProxyType` does **(V)**.
- `Decimal(0.1)` carries the float error; use `Decimal(str(x))` **(V)**.

**Possibilities**
- The same contract with different contexts in tests (loose and tight budget).
- A context with an injected clock (expiry dates) and the user profile.
