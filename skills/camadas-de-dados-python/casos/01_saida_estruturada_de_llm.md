# Caso 01 — Saída estruturada de LLM

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** o modelo devolve texto; o programa precisa de dados com forma e tipos.
**Desenho:** contrato Pydantic → JSON Schema no prompt (ou saída nativa) → **tipo de borda** que recebe o texto e devolve o
objeto validado. Texto só existe na borda, dentro de um tipo; a aplicação não toca em texto.

**Nível 1 — saída nativa (preferível quando o endpoint suporta):** o SDK entrega o objeto e não sobra texto nenhum.

```python
resposta = client.chat.completions.parse(model=..., messages=..., response_format=ListaDeCompras)
lista = resposta.choices[0].message.parsed      # ListaDeCompras, ou None se o modelo recusou
```

**Nível 2 — schema no prompt + tipo de borda (qualquer endpoint compatível):**

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

def extrair_json(texto):
    """Primeiro JSON (objeto ou lista) decodificável, como texto. Decodifica; não recorta."""
    if not isinstance(texto, str):
        return texto
    decoder = json.JSONDecoder()
    for inicio, caractere in enumerate(texto):
        if caractere in "{[":
            try:
                _, fim = decoder.raw_decode(texto, inicio)
            except json.JSONDecodeError:
                continue
            return texto[inicio:fim]
    raise ValueError("nenhum JSON decodificável na resposta")

@lru_cache(maxsize=None)
def saida_llm(modelo: type) -> TypeAdapter:
    """Tipo de borda: texto do LLM -> objeto validado. Um TypeAdapter por modelo."""
    return TypeAdapter(Annotated[Json[modelo], BeforeValidator(extrair_json)])

lista = saida_llm(ListaDeCompras).validate_python(texto)               # ListaDeCompras
itens = saida_llm(list[Ingrediente]).validate_python(texto)            # lista solta, se for o contrato
lista = saida_llm(ListaComContexto).validate_python(texto, context=ctx)  # o contexto atravessa a borda
```

Por que assim:
- `Json[Modelo]` recebe **texto JSON** e valida contra o modelo; o `BeforeValidator` tira antes o que vem em volta.
- "Sem JSON", JSON quebrado e campo inválido chegam **do mesmo jeito**: `ValidationError` com `loc` e `msg`, prontos para o
  retry ([caso 04](04_regras_de_negocio_e_retry_com_feedback.md)). Um único `except ValidationError`.
- `Json[...]` valida em **modo JSON**: com `strict=True`, `date` e `Decimal` vindos como texto passam. `json.loads` +
  `model_validate(dict)` valida em modo Python e, em strict, rejeita os mesmos campos (`date_type`, `is_instance_of`) **(V)**.
- `extrair_json` **decodifica** (`raw_decode`) a partir de cada `{`/`[`. Recortar da primeira `{` à última `}` é texto
  tratado como dado, e falha (tabela abaixo).

| Resposta do modelo | Recorte `{`…`}` | Decodificar (`raw_decode`) |
|---|---|---|
| cerca ```` ```json ```` em volta | ok | ok |
| texto depois com chaves (`troque {queijo}`) | `JSONDecodeError` | ok |
| texto antes com chaves (`Formato {a, b}:`) | `JSONDecodeError` | ok |
| dois objetos | `JSONDecodeError` | ok (pega o primeiro) |
| lista solta `[{...}]` | **`dict` do primeiro item, sem erro** | `list` |

Tudo **(V)** em Pydantic 2.13.5 e 2.14.3, junto com: borda devolve o modelo; "sem JSON" vira `value_error` em `loc=()`;
`context=` chega ao `model_validator`; `lru_cache` devolve o mesmo `TypeAdapter`.

| Jeito | Como | Funciona em |
|---|---|---|
| saída nativa | `client.chat.completions.parse(response_format=Modelo)` → `.parsed` | endpoints que suportam (testado em endpoint compatível) |
| pydantic-ai | `Agent(OpenAIChatModel(nome, provider=OpenAIProvider(base_url=, api_key=)), output_type=Modelo)` | idem, menos código |
| schema no prompt | `prompt_com_schema` + `saida_llm(Modelo).validate_python(texto)` | qualquer endpoint compatível |

**Pegadinhas**
- Formato pedido só no prompt não é garantido; quantidade em texto multiplica em silêncio (`'250 grams' * 2`) **(V)**.
- Resposta vem com texto ou cerca ```` ```json ```` em volta **(R)**: `model_validate_json` dá `json_invalid` **(V)**.
- Recortar da primeira `{` à última `}` quebra com prosa que tem chaves e transforma **lista solta em `dict` sem erro** **(V)**.
- `texto` circulando pela aplicação (`extrair_json` + `model_validate_json` espalhados) é texto fingindo ser dado: cada
  chamador esquece um caso, e "sem JSON" vira `ValueError` à parte. Centralize no tipo de borda.
- Com dois JSONs na resposta (exemplo + resposta), o decodificador pega **o primeiro** **(V)**: peça no prompt um JSON só e,
  se o modelo insistir, deixe a validação recusar o exemplo.
- Quantidade não numérica, como `"to taste"` **(R)**: o contrato precisa decidir (ver possibilidades).
- O modelo pode devolver uma **lista solta** em vez do objeto **(R)**: `Input should be an object` **(V)**.
- `description` é pedido, não regra: `unidade: str` com description "g, kg..." aceita `"cups"` **(V)**.
- Saída nativa strict: o default some do schema e o campo opcional vira obrigatório-nullable (`to_strict_json_schema`) **(V)**.
- pydantic-ai no Jupyter: `run_sync` levanta `RuntimeError: This event loop is already running`; use `await agente.run(...)` **(V)**.
- `pydantic_function_tool`/saída nativa geram `strict: true`; endpoints compatíveis podem ignorar: valide localmente sempre.

**Possibilidades**
- Lista solta como contrato: `saida_llm(list[Ingrediente])`; o `extrair_json` já aceita `[`.
- Borda como dataclass: `Json[MinhaDataclass]` também funciona; com `__pydantic_config__ = ConfigDict(extra="forbid")`
  um campo a mais dá `unexpected_keyword_argument` **(V)**.
- Quantidade opcional: `quantidade: float | None` + `a_gosto: bool`, ou união `float | Literal["a gosto"]`.
- `TestModel` do pydantic-ai para testar o encanamento sem rede.
- Gravar respostas reais em `respostas_gravadas/` e testá-las offline contra o contrato.
