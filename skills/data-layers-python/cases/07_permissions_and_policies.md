# Case 07 — Permissions and policies

[← SKILL.md](../SKILL.md) · [pitfalls](../pitfalls.md) · [reference](../reference/tools.md)

**Scenario:** who may do what; irreversible actions require human confirmation.
**Design:** a `Flag` of capabilities per profile; a tool → capability table; the decision as an enum; deny by default.

```python
class Capability(Flag):
    READ_PRICES = auto()
    READ_PANTRY = auto()
    CHECKOUT = auto()

class Decision(StrEnum):
    ALLOW = "allow"; DENY = "deny"; CONFIRM = "confirm_with_human"

def decide(profile: Profile, name: str) -> tuple[Decision, str]:
    try:
        tool = Tool(name)
    except ValueError:
        return Decision.DENY, f"unknown tool: {name}"
    required = REQUIRED_CAPABILITY.get(tool)
    if required is None:                                 # never .get(tool, Capability(0))
        return Decision.DENY, "no capability mapped"
    if profile not in PERMISSIONS or required not in PERMISSIONS[profile]:
        return Decision.DENY, f"profile {profile} lacks {required.name}"
    if required & NEEDS_CONFIRMATION:
        return Decision.CONFIRM, "irreversible action"
    return Decision.ALLOW, "ok"
```

An open enum that records the unknown value (version-independent):

```python
def accept_unknown(v):
    if isinstance(v, str) and v not in {m.value for m in Intent}:
        UNKNOWN_SEEN.append(v)
        return Intent.UNKNOWN
    return v

intent: Annotated[Intent, BeforeValidator(accept_unknown)]
```

**Pitfalls**
- `Flag(0) in X` is always `True`: a "harmless" default becomes full permission **(V)**.
- Pydantic 2.13.5: `model_validate_json` calls `Enum._missing_` with `None`; with a dict the value arrives; 2.14.3 fixed it **(V)**.
- `assert_never` only truly protects with mypy/pyright; at runtime it is an `AssertionError` **(V)**.
- A policy in the prompt is not a policy: the profile comes from the session, never from the user's text or the model **(V)**.

**Possibilities**
- The profile × tool matrix as a test (that is what is worth testing).
- A profile hierarchy by composing `Flag`s; an audit log of every decision.
