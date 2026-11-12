# Case 05 — Intent routing

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** requests of different kinds (recipe, price, substitution, out of scope).
**Design:** the model **classifies** (small output), a table **decides**; confidence threshold; tools per route.

```python
class Classification(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    dish: str | None = None
    ingredient: str | None = None

ROUTES: dict[Intent, Callable[[Classification], str]] = {
    Intent.RECIPE: answer_recipe,
    Intent.PRICE: answer_price,
    Intent.SUBSTITUTION: answer_substitution,
    Intent.OUT_OF_SCOPE: decline,
}
assert not set(Intent) - ROUTES.keys(), "intent without a route"
TOOLS_BY_ROUTE: dict[Intent, frozenset[Tool]] = {...}
assert TOOLS_BY_ROUTE.keys() == set(Intent)

def route(c: Classification) -> str:
    if c.confidence < CONFIDENCE_THRESHOLD:
        return "human review"
    return ROUTES[c.intent](c)
```

**Pitfalls**
- Confidence is self-reported, not calibrated: 0.90 on almost everything, 1.00 on "recommend me a movie" **(R)**; a mistake with 0.95 passes the threshold **(V)**.
- A missing route without a coverage test becomes a `KeyError` in production **(V)**.
- Changing the value `"preco"` to `"preço"` (accent added) breaks reading everything already stored **(V)**.
- An invented value (`"sweet_recipe"`) drops the whole classification **(V)** → open enum ([case 07](07_permissions_and_policies.md)).
- Sending only some tools does not stop the model from asking for another: check at execution time.

**Possibilities**
- An evaluation set (request → expected intent) and accuracy per intent.
- A human review queue for low confidence or `UNKNOWN`.
