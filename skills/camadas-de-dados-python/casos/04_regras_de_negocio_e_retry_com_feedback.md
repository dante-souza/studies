# Caso 04 — Regras de negócio e retry com feedback

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** a resposta passa no contrato mas viola regras (limites por pessoa, duplicados).
**Desenho:** regras como funções que devolvem `list[str]`; o pedido é validado **antes** da chamada; na violação, a
resposta e os erros voltam ao modelo, até um limite.

```python
@dataclass
class ResultadoPedido:
    lista: ListaDeCompras
    tentativas: int
    erros_por_tentativa: list[list[str]] = field(default_factory=list)

def pedir_lista(prato, porcoes, chamar_modelo, max_tentativas=3) -> ResultadoPedido:
    validar_pedido(prato, porcoes)                      # erro determinístico não gasta chamada
    mensagens, historico = [...], []
    for tentativa in range(1, max_tentativas + 1):
        texto = chamar_modelo(mensagens)
        lista, erros = erros_da_resposta(texto)          # contrato + regras
        historico.append(erros)
        if not erros:
            return ResultadoPedido(lista, tentativa, historico)   # saída 1: sucesso, no meio do laço
        mensagens += [{"role": "assistant", "content": texto},
                      {"role": "user", "content": "Corrija:\n- " + "\n- ".join(erros)}]
    raise RuntimeError(f"sem resposta válida em {max_tentativas} tentativas")  # saída 2: fracasso
```

**Pegadinhas**
- Regras fora do contrato: qualquer caminho que crie o modelo pula as regras **(V)**.
- Cada tentativa reenvia a conversa inteira: o tamanho enviado cresce a cada rodada **(V)**.
- Retry não conserta pedido ruim: valide a entrada antes **(V)**.
- `except ValidationError` antes de `except ValueError`: `ValidationError` é subclasse de `ValueError` **(V)**.

**Possibilidades**
- Levar as regras para dentro do contrato com contexto ([caso 06](06_contrato_com_contexto.md)).
- Corte do histórico por orçamento de tokens ([caso 08](08_runtime_estado_custo_tempo_e_historico.md)) e um modelo mais barato para a correção.
