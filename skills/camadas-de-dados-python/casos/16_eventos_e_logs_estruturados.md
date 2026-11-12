# Caso 16 — Eventos e logs estruturados

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** trilha de auditoria, eventos entre serviços, logs legíveis por máquina.
**Desenho:** evento como modelo (ou dict validado) com `tipo` e `versao`; JSONL sem cor no arquivo; cor só na leitura.

```python
class EventoPedidoV1(BaseModel):
    tipo: Literal["pedido"]
    versao: Literal[1]
    pedido: str
    status: Status

Evento = Annotated[EventoPedidoV1 | EventoPagamentoV1, Field(discriminator="tipo")]

with JsonlWriter("eventos.jsonl") as escritor:        # logger_general.py
    escritor.write(evento.model_dump(mode="json"))
view_file("eventos.jsonl", semantic_rules={"status": {"falhou": "bad"}})   # prettifier.py
```

**Pegadinhas**
- Códigos de cor gravados em arquivo estragam a leitura por máquina: grave limpo, colora ao ler **(V)**.
- Timestamp nos logs muda toda execução: notebooks e HTML gerados ficam com diff ruidoso **(V)**.
- Evento sem `versao` torna a evolução do formato um problema de adivinhação.

**Possibilidades**
- União discriminada por `tipo` e, dentro dela, por `versao`, com função de upgrade V1 → V2.
- Redação na hora de registrar (e-mail, cartão) e chave de correlação (hash do pedido).
