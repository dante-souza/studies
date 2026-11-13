# Case 09 — Full pipeline

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** everything together: environment settings, validated input, classification, route, list with context,
cache, log and tests.

```python
class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHOP_", env_file=find_dotenv(usecwd=True) or None,
                                      extra="ignore", validate_by_name=True)
    api_key: SecretStr = Field(validation_alias=AliasChoices("SHOP_API_KEY", "openai"))
    base_url: str = Field(default="https://api.openai.com/v1",
                          validation_alias=AliasChoices("SHOP_BASE_URL", "openai_base_url"))
    max_attempts: int = Field(default=3, ge=1, le=5)

class OrderRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    profile: Profile                     # from the session
    servings: int = Field(default=2, ge=1, le=20)
    budget: Decimal | None = Field(default=None, gt=0)

def cache_key(request: OrderRequest) -> str:   # everything that changes the answer goes into the key
    normalized = request.model_dump(mode="json") | {"text": " ".join(request.text.lower().split())}
    return hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()[:16]
```

Structured events (`order`, `status`, already-redacted `detail`) go to the console through the logger and to JSONL; a
simulated client with the same interface as `OpenAI(...)` for offline tests; switching to the real client is one line.

**Pitfalls**
- A cache key with only the text: a visitor receives the answer built for a customer **(V)**; a cache without TTL keeps stale prices.
- `str(SecretStr)` is `**********`; passing it to the client gives an authentication error far from the cause **(V)**.
- `validation_alias` + `extra="ignore"`: `AppSettings(api_key=...)` is silently ignored without `validate_by_name=True` **(V)**.
- Regex redaction misses unknown formats (`4111.1111...`, "ana at example dot com") **(V)**; better not to log raw text at all.
- Tests with a simulated model test the plumbing, not the model's quality.

**Possibilities**
- Evaluation with the real client measuring accuracy, not pass/fail.
- Idempotency with a TTL or invalidation by price-table version.
