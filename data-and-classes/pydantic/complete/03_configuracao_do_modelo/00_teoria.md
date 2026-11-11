# Seção 3 — Configuração do modelo: teoria

> Notebooks: [`02`](02_tratando_campos_extras.ipynb) campos extras · [`03`](03_coercao_strict_e_lax.ipynb) strict × lax ·
> [`04`](04_validando_valores_default.ipynb) validando defaults · [`05`](05_validando_atribuicoes.ipynb) validando atribuições ·
> [`06`](06_mutabilidade.ipynb) mutabilidade · [`07`](07_convertendo_numeros_em_strings.ipynb) números → strings ·
> [`08`](08_padronizando_strings.ipynb) padronizando strings · [`09`](09_tratando_enums_python.ipynb) enums ·
> projeto: [`10`](10_projeto.ipynb) · [`11`](11_projeto_solucao_instrutor.ipynb) · [`12`](12_projeto_solucao_comentada.ipynb)

## Ideia central

`model_config = ConfigDict(...)` muda o **comportamento do modelo inteiro** — quando validar, o que aceitar e o que fazer com o que sobra.
Em vez de repetir regras campo a campo, a política fica num lugar só (e, na seção 11, numa classe base herdada).

## Configurações vistas

| chave | padrão | efeito |
|---|---|---|
| `extra` | `"ignore"` | `"forbid"` rejeita chaves desconhecidas; `"allow"` guarda em `model_extra` |
| `strict` | `False` | sem coerção: `"10"` não vira `10`; em strict, `list` só aceita `list` (tupla é rejeitada) |
| `validate_default` | `False` | defaults também passam pelos validadores (útil quando o default é calculado ou pode estar errado) |
| `validate_assignment` | `False` | `obj.campo = valor` é validado (sem isso, qualquer valor é gravado) |
| `frozen` | `False` | instância imutável (atribuição levanta `ValidationError`) |
| `coerce_numbers_to_str` | `False` | permite `int`/`float` → `str` (por padrão, o Pydantic **não** converte número em string) |
| `str_strip_whitespace`, `str_to_lower`, `str_to_upper` | `False` | padronização de todas as strings do modelo |
| `use_enum_values` | `False` | guarda o **valor** do enum em vez do membro |

```
entrada ─► [extra?] ─► [strict/lax por campo] ─► [str_* padronização] ─► instância
                                                                          │
                       obj.x = v ─► [validate_assignment?] ─► [frozen?] ──┘
```

## Divergências encontradas na revisão

- O curso dizia que, em strict, **tupla → lista** ainda era aceito. No 2.13 as duas direções falham.
- Parágrafos de texto em células de código (davam `SyntaxError`) viraram markdown.
- Notas do próprio usuário sobre "List to Enum" e YAML (`myconfig.yaml`, `my_new_config.yaml`) foram mantidas e traduzidas; o
  comentário que dizia `BANANA` não batia com o YAML (`apple`).

## Projeto

Configurar o `Automobile` (`extra="forbid"`, strip de strings, `validate_default`, `validate_assignment`) e usar `Enum` para o tipo do
carro. A solução comentada revisa a tentativa original (o campo `type_` estava declarado duas vezes; vale a última declaração, o que
esconde o erro) e acrescenta os testes que o enunciado pedia.
