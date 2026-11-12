# Caso 13 — DTOs de API

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** API HTTP (FastAPI) com criação, atualização parcial e leitura.
**Desenho:** um modelo por direção; nunca expor o modelo interno.

```python
class ProdutoCriar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str = Field(min_length=1)
    preco: Decimal = Field(gt=0)
    categoria: Categoria

class ProdutoAtualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str | None = None
    preco: Decimal | None = Field(default=None, gt=0)

class ProdutoLer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    nome: str
    preco: Decimal
    categoria: Categoria

mudancas = atualizacao.model_dump(exclude_unset=True)   # só o que o cliente mandou
```

**Pegadinhas**
- `exclude` usa nomes de campo; passar o alias é ignorado em silêncio **(V)**.
- Ordem dos erros pode mudar entre versões (no 2.14, o erro de campo extra veio por último) **(V)**: teste o conteúdo, não a ordem.
- `model_validate(instancia)` devolve a mesma instância, sem copiar **(V)**.
- `exclude_unset` x `exclude_none`: `None` enviado de propósito (apagar valor) é diferente de campo ausente.

**Possibilidades**
- `response_model` separado do modelo de banco; `computed_field` para valores derivados na resposta.
- Schema OpenAPI gerado dos mesmos modelos que validam.
