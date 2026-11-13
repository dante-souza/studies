# Caso 07 — Permissões e políticas

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** quem pode o quê; ações irreversíveis pedem confirmação humana.
**Desenho:** `Flag` de capacidades por perfil; tabela ferramenta → capacidade; decisão em enum; negar por padrão.

```python
class Capacidade(Flag):
    LER_PRECOS = auto()
    LER_DESPENSA = auto()
    FINALIZAR_PEDIDO = auto()

class Decisao(StrEnum):
    PERMITIR = "permitir"; NEGAR = "negar"; CONFIRMAR = "confirmar_com_humano"

def decidir(perfil: Perfil, nome: str) -> tuple[Decisao, str]:
    try:
        ferramenta = Ferramenta(nome)
    except ValueError:
        return Decisao.NEGAR, f"ferramenta desconhecida: {nome}"
    exigida = CAPACIDADE_EXIGIDA.get(ferramenta)
    if exigida is None:                                  # nunca .get(ferramenta, Capacidade(0))
        return Decisao.NEGAR, "sem capacidade mapeada"
    if perfil not in PERMISSOES or exigida not in PERMISSOES[perfil]:
        return Decisao.NEGAR, f"perfil {perfil} não tem {exigida.name}"
    if exigida & EXIGE_CONFIRMACAO:
        return Decisao.CONFIRMAR, "ação irreversível"
    return Decisao.PERMITIR, "ok"
```

Enum aberto que registra o desconhecido (independe de versão):

```python
def aceitar_desconhecido(v):
    if isinstance(v, str) and v not in {m.value for m in Intencao}:
        DESCONHECIDOS.append(v)
        return Intencao.DESCONHECIDO
    return v

intencao: Annotated[Intencao, BeforeValidator(aceitar_desconhecido)]
```

**Pegadinhas**
- `Flag(0) in X` é sempre `True`: um default "inofensivo" vira permissão total **(V)**.
- Pydantic 2.13.5: `model_validate_json` chama `Enum._missing_` com `None`; com dict chega o valor; 2.14.3 corrigiu **(V)**.
- `assert_never` só protege de verdade com mypy/pyright; em tempo de execução é um `AssertionError` **(V)**.
- Política no prompt não é política: o perfil vem da sessão, nunca do texto do usuário ou do modelo **(V)**.

**Possibilidades**
- Matriz perfil × ferramenta como teste (é ela que vale testar).
- Hierarquia de perfis por composição de `Flag`; log de auditoria de cada decisão.
