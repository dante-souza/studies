# Case 02 — Vocabulary and scope guardrail

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** fields with free values (`"cups"`) and out-of-scope requests.
**Design:** enums in the contract; the model declares the request kind; the code handles each kind.

```python
class RequestType(StrEnum):
    RECIPE = "recipe"
    OUT_OF_SCOPE = "out_of_scope"

class AssistantReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: RequestType
    shopping_list: ShoppingList | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def kind_matches_content(self):
        if self.kind is RequestType.RECIPE and self.shopping_list is None:
            raise ValueError("kind 'recipe' requires 'shopping_list'")
        if self.kind is RequestType.OUT_OF_SCOPE and (self.shopping_list is not None or not self.reason):
            raise ValueError("kind 'out_of_scope' requires 'reason' and accepts no 'shopping_list'")
        return self

def handle(reply: AssistantReply) -> str:
    match reply.kind:
        case RequestType.RECIPE:
            return f"shopping list for {reply.shopping_list.dish}"
        case RequestType.OUT_OF_SCOPE:
            return f"I only help with groceries ({reply.reason})"
        case _:
            raise ValueError(f"unhandled kind: {reply.kind!r}")
```

**Pitfalls**
- An enum compares exact text: `"G"` and `" g"` fail **(V)**. Normalize case and spaces with a `BeforeValidator`; synonyms (`"grams"`) are a business decision.
- `match` without `case _` returns `None` silently when the enum gains a member **(V)**.
- An enum guarantees vocabulary, not common sense: 3 kg of salt for 2 people passes **(V)**.
- A `StrEnum` with a dict in its body raises `TypeError`; a plain `Enum` silently turns the dict into a member **(V)**.

**Possibilities**
- Order output by enum declaration order (`for c in Category`), like store aisles.
- Per-member metadata (label, color, limit) in a dict keyed by the enum, with a coverage test.
- An open enum (`UNKNOWN`) when dropping the whole request is worse than sending it to a safe route ([case 07](07_permissions_and_policies.md)).
