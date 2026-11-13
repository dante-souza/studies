# Case 16 — Events and structured logs

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** audit trail, events between services, machine-readable logs.
**Design:** an event as a model (or a validated dict) with `kind` and `version`; JSONL without color in the file; color
only when reading.

```python
class OrderEventV1(BaseModel):
    kind: Literal["order"]
    version: Literal[1]
    order: str
    status: Status

Event = Annotated[OrderEventV1 | PaymentEventV1, Field(discriminator="kind")]

with JsonlWriter("events.jsonl") as writer:        # logger_general.py
    writer.write(event.model_dump(mode="json"))
view_file("events.jsonl", semantic_rules={"status": {"failed": "bad"}})   # prettifier.py
```

**Pitfalls**
- Color codes written to a file spoil machine reading: write clean, color when reading **(V)**.
- Log timestamps change on every run: generated notebooks and HTML get noisy diffs **(V)**.
- An event without `version` turns format evolution into guesswork.

**Possibilities**
- A union discriminated by `kind` and, inside it, by `version`, with a V1 → V2 upgrade function.
- Redaction at logging time (e-mail, card) and a correlation key (hash of the order).
