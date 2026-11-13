# Case 13 — API DTOs

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** HTTP API (FastAPI) with create, partial update and read.
**Design:** one model per direction; never expose the internal model.

```python
class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    price: Decimal = Field(gt=0)
    category: Category

class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    price: Decimal | None = Field(default=None, gt=0)

class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    price: Decimal
    category: Category

changes = update.model_dump(exclude_unset=True)   # only what the client sent
```

**Pitfalls**
- `exclude` uses field names; passing the alias is silently ignored **(V)**.
- Error order may change between versions (in 2.14 the extra-field error came last) **(V)**: test the content, not the order.
- `model_validate(instance)` returns the same instance, without copying **(V)**.
- `exclude_unset` vs `exclude_none`: a `None` sent on purpose (clear the value) is different from a missing field.

**Possibilities**
- A `response_model` separate from the database model; `computed_field` for derived values in the response.
- OpenAPI schema generated from the same models that validate.
