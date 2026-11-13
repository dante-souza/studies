# Referência rápida: Enum, Pydantic e dataclass

[← SKILL.md](../SKILL.md)

## Enum

| Tipo | Quando | Observação |
|---|---|---|
| `StrEnum` | valores de texto que vão para JSON, prompt, banco | membro **é** `str`: compara com texto, aparece como texto em f-string |
| `IntEnum` | códigos numéricos legados | compara com `int` (pode mascarar erro de tipo) |
| `Enum` | identidade pura, sem igualdade com primitivo | `Enum("x") == "x"` é `False` |
| `Flag` | permissões e capacidades combináveis | `A \| B`, `in`; cuidado com `Flag(0)` |
| `Literal[...]` | vocabulário local de um único modelo | sem comportamento nem reuso; enum quando o vocabulário circula |

## Pydantic (v2)

| Recurso | Uso |
|---|---|
| `ConfigDict(extra="forbid")` | entrada não confiável: chave desconhecida é erro |
| `ConfigDict(frozen=True)` | modelo imutável e hashable (se os campos forem) |
| `ConfigDict(strict=True)` / `Strict()` | sem conversão (`"1"` não vira `1`) |
| `ConfigDict(validate_default=True)` | defaults também passam pela validação |
| `ConfigDict(from_attributes=True)` | ler objetos (ORM) por atributo |
| `ConfigDict(validate_by_name=True)` | aceitar o nome do campo além do alias |
| `Field(gt=, le=, pattern=, description=)` | restrições; `description` vai para o JSON Schema |
| `BeforeValidator` / `AfterValidator` | normalizar antes / regra depois do tipo |
| `model_validator(mode="after")` | regra entre campos; recebe `ValidationInfo` (contexto) |
| `PrivateAttr` | valor calculado guardado no objeto, fora do schema |
| `TypeAdapter(T)` | validar tipos que não são modelos (`list[Item]`, dataclass) |
| `BaseSettings` | configuração de env e `.env`, com `SecretStr` |
| `model_dump(mode="json")` | dict seguro para JSON (Decimal, date, enum como valor) |
| `model_json_schema()` | contrato para documentação e para prompt de LLM |

Ordem de execução: `BeforeValidator` (vários: ordem **reversa**) → tipo e restrições do `Field` → `AfterValidator` →
`model_validator(mode="after")`.

## dataclass

| Recurso | Uso |
|---|---|
| `frozen=True` | imutável e hashable; raso |
| `slots=True` | menos memória, atributos fixos; recria a classe |
| `kw_only=True` | construtor só por nome (evita troca de posição) |
| `field(default_factory=...)` | default mutável |
| `__post_init__` | **invariantes** do núcleo, não validação de entrada |
| `dataclasses.replace(obj, x=...)` | cópia alterada de objeto frozen |
| `asdict` | exporta recursivamente (copia tudo; caro em objetos grandes) |
