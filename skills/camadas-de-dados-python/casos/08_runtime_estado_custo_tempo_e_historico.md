# Caso 08 — Runtime: estado, custo, tempo e histórico

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** quantas chamadas, tokens, custo, tempo; conversa que cresce sem limite.
**Desenho:** dataclasses: config `frozen`, `Uso` (tokens), `Span`/`Rastreio` (`perf_counter`), `Historico` que envia
turnos inteiros dentro de um orçamento.

```python
@dataclass(frozen=True)
class ConfigRuntime:
    modelo: str = "gpt-4o-mini"
    max_rodadas: int = 5
    orcamento_tokens_envio: int = 4000
    preco_entrada_por_milhao: Decimal = Decimal("0.15")   # ilustrativo: use a tabela do provedor

@dataclass
class Historico:
    sistema: dict
    mensagens: list[dict] = field(default_factory=list)
    def turnos(self) -> list[list[dict]]: ...          # um turno começa em cada mensagem "user"
    def para_envio(self, orcamento: int) -> list[dict]: ...   # sistema + turnos recentes que cabem
```

**Pegadinhas**
- Cortar o histórico por número de mensagens pode começar num `tool` órfão; a API recusa **(V)**.
- Lista como default de dataclass é bloqueada na criação da classe **(V)**.
- `Decimal * float` levanta `TypeError` **(V)**.
- Dataclass não valida: `ConfigRuntime(max_rodadas="cinco")` passa e quebra só no `range`, longe da causa **(V)**.
- Tokens estimados (caracteres/4) servem para cortar antes de enviar; custo usa `resposta.usage` real.
- Duração com `perf_counter` (monótono), não `time.time()`.

**Possibilidades**
- `slots=True` em objetos numerosos; `dataclasses.replace` para variantes de config.
- IDs de tool call únicos no cliente simulado, como na API real.
