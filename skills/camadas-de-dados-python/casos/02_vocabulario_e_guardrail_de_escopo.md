# Caso 02 — Vocabulário e guardrail de escopo

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** campos com valores livres (`"cups"`) e pedidos fora do escopo.
**Desenho:** enums no contrato; o modelo declara o tipo do pedido; o código trata cada tipo.

```python
class TipoPedido(StrEnum):
    RECEITA = "receita"
    FORA_DO_ESCOPO = "fora_do_escopo"

class RespostaAssistente(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: TipoPedido
    lista: ListaDeCompras | None = None
    motivo: str | None = None

    @model_validator(mode="after")
    def tipo_combina_com_conteudo(self):
        if self.tipo is TipoPedido.RECEITA and self.lista is None:
            raise ValueError("tipo 'receita' exige 'lista'")
        if self.tipo is TipoPedido.FORA_DO_ESCOPO and (self.lista is not None or not self.motivo):
            raise ValueError("tipo 'fora_do_escopo' exige 'motivo' e não aceita 'lista'")
        return self

def tratar(r: RespostaAssistente) -> str:
    match r.tipo:
        case TipoPedido.RECEITA:
            return f"lista de {r.lista.prato}"
        case TipoPedido.FORA_DO_ESCOPO:
            return f"só ajudo com compras ({r.motivo})"
        case _:
            raise ValueError(f"tipo sem tratamento: {r.tipo!r}")
```

**Pegadinhas**
- Enum compara texto exato: `"G"` e `" g"` falham **(V)**. Normalize caixa e espaços com `BeforeValidator`; sinônimos (`"gramas"`) são decisão de negócio.
- `match` sem `case _` devolve `None` em silêncio quando o enum ganha membro **(V)**.
- Enum garante vocabulário, não bom senso: 3 kg de sal para 2 pessoas passa **(V)**.
- `StrEnum` com um dict no corpo levanta `TypeError`; `Enum` comum transforma o dict em membro em silêncio **(V)**.

**Possibilidades**
- Organizar saída pela ordem de declaração do enum (`for c in Categoria`), como seções do mercado.
- Metadados por membro (rótulo, cor, limite) em dict indexado pelo enum, com teste de cobertura.
- Enum aberto (`DESCONHECIDO`) quando derrubar o pedido inteiro é pior que mandar para uma rota segura ([caso 07](07_permissoes_e_politicas.md)).
