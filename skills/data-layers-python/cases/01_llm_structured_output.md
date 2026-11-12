# Case 01 — LLM structured output

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** the model returns text; the program needs data with shape and types.
**Design:** Pydantic contract → JSON Schema in the prompt (or native output) → extract the JSON → validate.

```python
class Ingredient(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    quantity: float = Field(gt=0, description="Number, no unit")
    unit: Unit

class ShoppingList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dish: str
    servings: int = Field(gt=0)
    ingredients: list[Ingredient]

def prompt_with_schema(instruction: str, model: type[BaseModel]) -> str:
    return (f"{instruction}\nAnswer ONLY with valid JSON that follows this JSON Schema:\n"
            f"{json.dumps(model.model_json_schema(), ensure_ascii=False)}")

def extract_json(text: str) -> str:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in the response")
    return text[start:end + 1]

shopping_list = ShoppingList.model_validate_json(extract_json(reply))
```

| Approach | How | Works on |
|---|---|---|
| schema in the prompt | `prompt_with_schema` + `model_validate_json` | any compatible endpoint |
| native output | `client.chat.completions.parse(response_format=Model)` → `.parsed` | endpoints that support it (tested on a compatible endpoint) |
| pydantic-ai | `Agent(OpenAIChatModel(name, provider=OpenAIProvider(base_url=, api_key=)), output_type=Model)` | same, less code |

**Pitfalls**
- A format requested only in the prompt is not guaranteed; a quantity as text multiplies silently (`'250 grams' * 2`) **(V)**.
- The response comes wrapped in text or a ```` ```json ```` fence **(R)**: `model_validate_json` gives `json_invalid`; extract first **(V)**.
- Non-numeric quantity, such as `"to taste"` **(R)**: the contract has to decide (see possibilities).
- The model may return a **bare list** instead of the object **(R)**: `Input should be an object` **(V)**.
- `description` is a request, not a rule: `unit: str` with description "g, kg..." accepts `"cups"` **(V)**.
- Native strict output: the default disappears from the schema and an optional field becomes required-nullable (`to_strict_json_schema`) **(V)**.
- pydantic-ai in Jupyter: `run_sync` raises `RuntimeError: This event loop is already running`; use `await agent.run(...)` **(V)**.
- `pydantic_function_tool`/native output emit `strict: true`; compatible endpoints may ignore it: always validate locally.

**Possibilities**
- Bare list: `TypeAdapter(list[Ingredient]).validate_json(...)` and, in `extract_json`, consider `[`.
- Optional quantity: `quantity: float | None` + `to_taste: bool`, or the union `float | Literal["to taste"]`.
- pydantic-ai's `TestModel` to test the plumbing without network.
- Record real responses in `recorded_responses/` and test them offline against the contract.
