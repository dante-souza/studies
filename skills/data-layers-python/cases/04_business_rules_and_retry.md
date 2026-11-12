# Case 04 — Business rules and retry with feedback

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** the response passes the contract but breaks rules (per-person limits, duplicates).
**Design:** rules as functions that return `list[str]`; the request is validated **before** the call; on a violation, the
response and the errors go back to the model, up to a limit.

```python
@dataclass
class OrderResult:
    shopping_list: ShoppingList
    attempts: int
    errors_per_attempt: list[list[str]] = field(default_factory=list)

def request_list(dish, servings, call_model, max_attempts=3) -> OrderResult:
    validate_request(dish, servings)                    # a deterministic error does not spend a call
    messages, history = [...], []
    for attempt in range(1, max_attempts + 1):
        text = call_model(messages)
        shopping_list, errors = response_errors(text)   # contract + rules
        history.append(errors)
        if not errors:
            return OrderResult(shopping_list, attempt, history)   # exit 1: success, mid-loop
        messages += [{"role": "assistant", "content": text},
                     {"role": "user", "content": "Fix:\n- " + "\n- ".join(errors)}]
    raise RuntimeError(f"no valid response in {max_attempts} attempts")  # exit 2: failure
```

**Pitfalls**
- Rules outside the contract: any path that creates the model skips the rules **(V)**.
- Each attempt resends the whole conversation: the payload grows every round **(V)**.
- Retry does not fix a bad request: validate the input first **(V)**.
- `except ValidationError` before `except ValueError`: `ValidationError` is a subclass of `ValueError` **(V)**.

**Possibilities**
- Move the rules into the contract with context ([case 06](06_contract_with_context.md)).
- Cut the history by a token budget ([case 08](08_runtime_state_cost_time_history.md)) and use a cheaper model for the repair.
