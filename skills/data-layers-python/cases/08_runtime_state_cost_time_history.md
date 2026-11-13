# Case 08 — Runtime: state, cost, time and history

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** how many calls, tokens, cost, time; a conversation that grows without limit.
**Design:** dataclasses: `frozen` config, `Usage` (tokens), `Span`/`Trace` (`perf_counter`), a `History` that sends whole
turns within a budget.

```python
@dataclass(frozen=True)
class RuntimeConfig:
    model: str = "gpt-4o-mini"
    max_rounds: int = 5
    send_token_budget: int = 4000
    input_price_per_million: Decimal = Decimal("0.15")   # illustrative: use your provider's price table

@dataclass
class History:
    system: dict
    messages: list[dict] = field(default_factory=list)
    def turns(self) -> list[list[dict]]: ...          # a turn starts at each "user" message
    def to_send(self, budget: int) -> list[dict]: ... # system + the most recent turns that fit
```

**Pitfalls**
- Cutting the history by message count may start at an orphan `tool` message; the API rejects it **(V)**.
- A list as a dataclass default is blocked when the class is created **(V)**.
- `Decimal * float` raises `TypeError` **(V)**.
- A dataclass does not validate: `RuntimeConfig(max_rounds="five")` passes and breaks only at `range`, far from the cause **(V)**.
- Estimated tokens (characters/4) are for cutting before sending; cost uses the real `response.usage`.
- Measure durations with `perf_counter` (monotonic), not `time.time()`.

**Possibilities**
- `slots=True` for numerous objects; `dataclasses.replace` for config variants.
- Unique tool call IDs in the simulated client, as in the real API.
