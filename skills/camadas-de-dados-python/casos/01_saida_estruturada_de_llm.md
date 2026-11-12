# Caso 01 — Saída estruturada de LLM

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** o modelo devolve texto; o programa precisa de dados com forma e tipos.
**Desenho:** contrato Pydantic → JSON Schema no prompt (ou saída nativa) → extrair o JSON → validar.

```python
class Ingrediente(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str
    quantidade: float = Field(gt=0, description="Número, sem unidade")
    unidade: Unidade

class ListaDeCompras(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prato: str
    porcoes: int = Field(gt=0)
    ingredientes: list[Ingrediente]

def prompt_com_schema(instrucao: str, modelo: type[BaseModel]) -> str:
    return (f"{instrucao}\nResponda SOMENTE com um JSON válido que siga este JSON Schema:\n"
            f"{json.dumps(modelo.model_json_schema(), ensure_ascii=False)}")

def extrair_json(texto: str) -> str:
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("nenhum objeto JSON na resposta")
    return texto[inicio:fim + 1]

lista = ListaDeCompras.model_validate_json(extrair_json(resposta))
```

| Jeito | Como | Funciona em |
|---|---|---|
| schema no prompt | `prompt_com_schema` + `model_validate_json` | qualquer endpoint compatível |
| saída nativa | `client.chat.completions.parse(response_format=Modelo)` → `.parsed` | endpoints que suportam (testado em endpoint compatível) |
| pydantic-ai | `Agent(OpenAIChatModel(nome, provider=OpenAIProvider(base_url=, api_key=)), output_type=Modelo)` | idem, menos código |

**Pegadinhas**
- Formato pedido só no prompt não é garantido; quantidade em texto multiplica em silêncio (`'250 grams' * 2`) **(V)**.
- Resposta vem com texto ou cerca ```` ```json ```` em volta **(R)**: `model_validate_json` dá `json_invalid`; extraia antes **(V)**.
- Quantidade não numérica, como `"to taste"` **(R)**: o contrato precisa decidir (ver possibilidades).
- O modelo pode devolver uma **lista solta** em vez do objeto **(R)**: `Input should be an object` **(V)**.
- `description` é pedido, não regra: `unidade: str` com description "g, kg..." aceita `"cups"` **(V)**.
- Saída nativa strict: o default some do schema e o campo opcional vira obrigatório-nullable (`to_strict_json_schema`) **(V)**.
- pydantic-ai no Jupyter: `run_sync` levanta `RuntimeError: This event loop is already running`; use `await agente.run(...)` **(V)**.
- `pydantic_function_tool`/saída nativa geram `strict: true`; endpoints compatíveis podem ignorar: valide localmente sempre.

**Possibilidades**
- Lista solta: `TypeAdapter(list[Ingrediente]).validate_json(...)` e, em `extrair_json`, considerar `[`.
- Quantidade opcional: `quantidade: float | None` + `a_gosto: bool`, ou união `float | Literal["a gosto"]`.
- `TestModel` do pydantic-ai para testar o encanamento sem rede.
- Gravar respostas reais em `respostas_gravadas/` e testá-las offline contra o contrato.
