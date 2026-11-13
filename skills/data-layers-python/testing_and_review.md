# Testing and review

[← SKILL.md](SKILL.md)

## Anti-patterns

- One single model for input, database and response.
- A loose `dict` crossing layers ("bag of data").
- Validating in the middle of the core, again and again.
- A rule that lives only in the prompt, only in the `description` or only in a comment.
- `Any` and `extra="allow"` at the border without a recorded reason.
- `except Exception: pass` while parsing.
- An enum whose value is display text (it changes with the UI; the value should be stable).
- `__post_init__` acting as validation of external input.

## Testing strategy

- **Enum coverage:** every table keyed by an enum covers all members.
- **Policy matrix:** profile × action → expected decision.
- **Round trip:** `Model.model_validate(obj.model_dump(mode="json")) == obj`.
- **One pitfall per test:** each relevant catalog item becomes a test that would fail without the remedy.
- **Messages, not order:** compare sets of errors (`{(e["loc"], e["type"]) for e in ex.errors()}`).
- **Offline LLM:** a simulated client with the SDK interface (`.chat.completions.create` returning the SDK types) and scripts that fail on purpose.
- **Real LLM:** an evaluation set with expected answers; measure accuracy; record real responses for regression.
- **Versions:** run the suite on two Pydantic versions when the behavior matters.

## Review checklist

- [ ] Every piece of data has a clear origin and the right tool (border x core).
- [ ] External input with `extra="forbid"` (or a recorded reason not to).
- [ ] Closed vocabularies are enums; values treated as an external contract.
- [ ] Normalization in `BeforeValidator`; rules in `AfterValidator`/`model_validator`.
- [ ] Request-dependent rules use `context=` and fail without context.
- [ ] LLM or API text only enters through a border type; no string slicing, no `text` passed along.
- [ ] Money in `Decimal`, built from text.
- [ ] Core in dataclasses; frozen where it does not change; internal collections protected.
- [ ] Enum-keyed tables with coverage tests; `match` with `case _`.
- [ ] Permissions deny by default; the profile comes from the session.
- [ ] Secrets in `SecretStr`; never in logs, `repr` or JSON.
- [ ] Validation errors become useful messages (for the user or the LLM).
- [ ] Logs and JSONL without sensitive data and without color codes.
- [ ] Tests cover the relevant pitfalls; what was not tested is stated.
