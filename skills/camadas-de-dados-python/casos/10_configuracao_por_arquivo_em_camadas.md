# Caso 10 — Configuração por arquivo, em camadas

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** `base.yaml` + `prod.yaml` + variáveis de ambiente, com segredos.
**Desenho:** carregar cada fonte, mesclar em camadas, validar **uma vez** com Pydantic; segredos só por ambiente.

| Formato | Tipos nativos | Cuidado |
|---|---|---|
| JSON | número, bool, null, lista, objeto | sem comentários |
| TOML | inclui datas e inteiros/floats distintos | `tomllib` só lê |
| YAML | tudo, implícito | YAML 1.1 (PyYAML): `no`/`off` viram `False`, `3.10` vira `3.1`; `"3.10"` com aspas fica texto **(V)**; use `safe_load` |
| INI | só texto | toda conversão é sua (ou do Pydantic) |
| `.env` | só texto | aspas e espaços variam entre bibliotecas |

```python
def mesclar(base: dict, extra: dict) -> dict:
    resultado = dict(base)
    for chave, valor in extra.items():
        if valor is None and isinstance(base.get(chave), dict):
            raise ValueError(f"'{chave}: null' apagaria a seção inteira")
        if isinstance(valor, dict) and isinstance(base.get(chave), dict):
            resultado[chave] = mesclar(base[chave], valor)
        else:
            resultado[chave] = valor
    return resultado

config = TypeAdapter(AppConfig).validate_python(mesclar(base, prod))
```

**Pegadinhas**
- `deep_merge` ingênuo: `secao: null` no arquivo de produção apaga a seção inteira **(V)**.
- Dataclass via `TypeAdapter` ignora chaves extras (erro de digitação some): `__pydantic_config__ = {"extra": "forbid"}` **(V)**, que propaga para dataclasses aninhadas; `TypeAdapter(config=...)` é recusado para dataclass **(V)**.
- `strict=True` com dataclass aninhada exige instância exata (BaseModel aceita dict) **(V)**.
- Defaults não são validados: um default enum escrito como `2` continua `int` **(V)**.

**Possibilidades**
- Precedência explícita: argumentos > ambiente > `.env` > arquivo > default (`BaseSettings` já segue boa parte).
- Políticas e presets em arquivo (`ConfigDict` vindo de YAML, validado antes de aplicar).
