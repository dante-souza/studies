# Case 01 — LLM structured output

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** the model returns text; the program needs data with shape and types.
**Design:** Pydantic contract → JSON Schema in the prompt (or native output) → a **border type** that takes the text and
returns the validated object. Text only exists at the border, inside a type; the application does not touch text.

**Level 1 — native output (preferred when the endpoint supports it):** the SDK hands over the object and no text is left.

```python
response = client.chat.completions.parse(model=..., messages=..., response_format=ShoppingList)
shopping_list = response.choices[0].message.parsed      # ShoppingList, or None if the model refused
```

**Level 2 — schema in the prompt + border type (any compatible endpoint):**

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

def extract_json(text):
    """First decodable JSON (object or list), as text. Decodes; does not slice."""
    if not isinstance(text, str):
        return text
    decoder = json.JSONDecoder()
    for start, char in enumerate(text):
        if char in "{[":
            try:
                _, end = decoder.raw_decode(text, start)
            except json.JSONDecodeError:
                continue
            return text[start:end]
    raise ValueError("no decodable JSON in the response")

@lru_cache(maxsize=None)
def llm_output(model: type) -> TypeAdapter:
    """Border type: LLM text -> validated object. One TypeAdapter per model."""
    return TypeAdapter(Annotated[Json[model], BeforeValidator(extract_json)])

shopping_list = llm_output(ShoppingList).validate_python(text)                    # ShoppingList
items = llm_output(list[Ingredient]).validate_python(text)                         # bare list, if that is the contract
shopping_list = llm_output(ShoppingListInContext).validate_python(text, context=ctx)  # the context crosses the border
```

Why this way:
- `Json[Model]` takes **JSON text** and validates it against the model; the `BeforeValidator` first strips what surrounds it.
- "No JSON", broken JSON and an invalid field all arrive **the same way**: a `ValidationError` with `loc` and `msg`, ready for
  the retry ([case 04](04_business_rules_and_retry.md)). A single `except ValidationError`.
- `Json[...]` validates in **JSON mode**: with `strict=True`, `date` and `Decimal` sent as text pass. `json.loads` +
  `model_validate(dict)` validates in Python mode and, in strict, rejects the same fields (`date_type`, `is_instance_of`) **(V)**.
- `extract_json` **decodes** (`raw_decode`) from each `{`/`[`. Slicing from the first `{` to the last `}` is text treated as
  data, and it fails (table below).

| Model response | Slice `{`…`}` | Decode (`raw_decode`) |
|---|---|---|
| ```` ```json ```` fence around it | ok | ok |
| text after with braces (`swap {cheese}`) | `JSONDecodeError` | ok |
| text before with braces (`Format {a, b}:`) | `JSONDecodeError` | ok |
| two objects | `JSONDecodeError` | ok (takes the first) |
| bare list `[{...}]` | **`dict` of the first item, no error** | `list` |

All **(V)** on Pydantic 2.13.5 and 2.14.3, together with: the border returns the model; "no JSON" becomes `value_error` at
`loc=()`; `context=` reaches the `model_validator`; `lru_cache` returns the same `TypeAdapter`.

| Approach | How | Works on |
|---|---|---|
| native output | `client.chat.completions.parse(response_format=Model)` → `.parsed` | endpoints that support it (tested on a compatible endpoint) |
| pydantic-ai | `Agent(OpenAIChatModel(name, provider=OpenAIProvider(base_url=, api_key=)), output_type=Model)` | same, less code |
| schema in the prompt | `prompt_with_schema` + `llm_output(Model).validate_python(text)` | any compatible endpoint |

**Pitfalls**
- A format requested only in the prompt is not guaranteed; a quantity as text multiplies silently (`'250 grams' * 2`) **(V)**.
- The response comes wrapped in text or a ```` ```json ```` fence **(R)**: `model_validate_json` gives `json_invalid` **(V)**.
- Slicing from the first `{` to the last `}` breaks on prose with braces and turns a **bare list into a `dict` with no error** **(V)**.
- `text` travelling through the application (`extract_json` + `model_validate_json` scattered around) is text pretending to
  be data: each caller forgets a case, and "no JSON" becomes a separate `ValueError`. Centralize it in the border type.
- With two JSONs in the response (example + answer), the decoder takes **the first** **(V)**: ask for a single JSON in the
  prompt and, if the model insists, let validation reject the example.
- Non-numeric quantity, such as `"to taste"` **(R)**: the contract has to decide (see possibilities).
- The model may return a **bare list** instead of the object **(R)**: `Input should be an object` **(V)**.
- `description` is a request, not a rule: `unit: str` with description "g, kg..." accepts `"cups"` **(V)**.
- Native strict output: the default disappears from the schema and an optional field becomes required-nullable (`to_strict_json_schema`) **(V)**.
- pydantic-ai in Jupyter: `run_sync` raises `RuntimeError: This event loop is already running`; use `await agent.run(...)` **(V)**.
- `pydantic_function_tool`/native output emit `strict: true`; compatible endpoints may ignore it: always validate locally.

**Possibilities**
- Bare list as the contract: `llm_output(list[Ingredient])`; `extract_json` already accepts `[`.
- Border as a dataclass: `Json[MyDataclass]` works too; with `__pydantic_config__ = ConfigDict(extra="forbid")`
  an extra field gives `unexpected_keyword_argument` **(V)**.
- Optional quantity: `quantity: float | None` + `to_taste: bool`, or the union `float | Literal["to taste"]`.
- pydantic-ai's `TestModel` to test the plumbing without network.
- Record real responses in `recorded_responses/` and test them offline against the contract.
