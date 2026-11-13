# Caso 05 — Roteamento por intenção

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** pedidos de tipos diferentes (receita, preço, substituição, fora do escopo).
**Desenho:** o modelo **classifica** (saída pequena), uma tabela **decide**; limiar de confiança; ferramentas por rota.

```python
class Classificacao(BaseModel):
    intencao: Intencao
    confianca: float = Field(ge=0, le=1)
    prato: str | None = None
    ingrediente: str | None = None

ROTAS: dict[Intencao, Callable[[Classificacao], str]] = {
    Intencao.RECEITA: responder_receita,
    Intencao.PRECO: responder_preco,
    Intencao.SUBSTITUICAO: responder_substituicao,
    Intencao.FORA_DO_ESCOPO: recusar,
}
assert not set(Intencao) - ROTAS.keys(), "intenção sem rota"
FERRAMENTAS_POR_ROTA: dict[Intencao, frozenset[Ferramenta]] = {...}
assert FERRAMENTAS_POR_ROTA.keys() == set(Intencao)

def rotear(c: Classificacao) -> str:
    if c.confianca < LIMIAR_CONFIANCA:
        return "revisão humana"
    return ROTAS[c.intencao](c)
```

**Pegadinhas**
- A confiança é autodeclarada, não calibrada: 0.90 em quase tudo, 1.00 em "me indica um filme" **(R)**; um erro com 0.95 passa pelo limiar **(V)**.
- Rota faltando sem teste de cobertura vira `KeyError` em produção **(V)**.
- Trocar o valor `"preco"` por `"preço"` quebra a leitura de tudo que foi gravado **(V)**.
- Valor inventado (`"receita_doce"`) derruba a classificação inteira **(V)** → enum aberto ([caso 07](07_permissoes_e_politicas.md)).
- Enviar só algumas ferramentas não impede o modelo de pedir outra: confira na execução.

**Possibilidades**
- Conjunto de avaliação (pedido → intenção esperada) e taxa de acerto por intenção.
- Fila de revisão humana para baixa confiança ou `DESCONHECIDO`.
