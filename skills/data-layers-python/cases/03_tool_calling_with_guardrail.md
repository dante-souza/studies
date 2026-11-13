# Case 03 — Tool calling with a guardrail

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** the model needs real data (prices, stock); the code is what executes.
**Design:** an enum with the closed list of tools; one Pydantic model per argument set; an executor that checks everything
and returns errors as results.

```python
class Tool(StrEnum):
    GET_PRICE = "get_price"
    CHECK_PANTRY = "check_pantry"

class IngredientArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str

REGISTRY = {Tool.GET_PRICE: (IngredientArgs, get_price),
            Tool.CHECK_PANTRY: (IngredientArgs, check_pantry)}
TOOLS = [openai.pydantic_function_tool(args, name=t.value, description=DESCRIPTIONS[t])
         for t, (args, _) in REGISTRY.items()]

def run_tool(name: str, arguments_json: str) -> str:
    try:
        tool = Tool(name)
    except ValueError:
        return json.dumps({"error": f"unknown tool: {name}"})
    args_model, function = REGISTRY[tool]
    try:
        args = args_model.model_validate_json(arguments_json)
    except ValidationError as ex:
        return json.dumps({"error": "invalid arguments", "details": ex.errors(include_url=False)},
                          ensure_ascii=False, default=str)
    return json.dumps(function(**args.model_dump()), ensure_ascii=False)
```

The loop: `call_model` is a parameter (real API or script); the round limit lives in a `frozen` dataclass; each result
goes back as a `role="tool"` message with its `tool_call_id`.

**Pitfalls**
- Without `max_rounds`, a model that keeps asking for tools never finishes **(V)**.
- Exact-name lookup: the model looked up `"tomate"` (tomato) while the table had `"tomate italiano"` (Italian tomato) **(R)**.
- `float` for money accumulates error (`0.10 + 0.20 = 0.30000000000000004`) **(V)**.
- The tool result goes back into the prompt: data from an external source is untrusted input.
- `message.model_dump(exclude_none=True)` when resending the assistant message: compatible endpoints may reject `None` fields.

**Possibilities**
- Canonical keys (`slug`) and a synonym table; or a search tool that returns candidates.
- Tools per route (least privilege, [case 05](05_intent_routing.md)) and per profile ([case 07](07_permissions_and_policies.md)).
- Arguments as a discriminated union when one tool has modes.
