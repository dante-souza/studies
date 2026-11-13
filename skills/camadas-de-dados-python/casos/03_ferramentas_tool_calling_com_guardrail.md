# Caso 03 — Ferramentas (tool calling) com guardrail

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** o modelo precisa de dados reais (preços, estoque); quem executa é o código.
**Desenho:** enum com a lista fechada de ferramentas; um modelo Pydantic por conjunto de argumentos; execução que confere
tudo e devolve erro como resultado.

```python
class Ferramenta(StrEnum):
    CONSULTAR_PRECO = "consultar_preco"
    VERIFICAR_DESPENSA = "verificar_despensa"

class ArgsIngrediente(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str

FERRAMENTAS = {Ferramenta.CONSULTAR_PRECO: (ArgsIngrediente, consultar_preco),
               Ferramenta.VERIFICAR_DESPENSA: (ArgsIngrediente, verificar_despensa)}
TOOLS = [openai.pydantic_function_tool(args, name=f.value, description=DESCRICOES[f])
         for f, (args, _) in FERRAMENTAS.items()]

def executar_ferramenta(nome: str, argumentos_json: str) -> str:
    try:
        ferramenta = Ferramenta(nome)
    except ValueError:
        return json.dumps({"erro": f"ferramenta desconhecida: {nome}"})
    modelo_args, funcao = FERRAMENTAS[ferramenta]
    try:
        args = modelo_args.model_validate_json(argumentos_json)
    except ValidationError as ex:
        return json.dumps({"erro": "argumentos inválidos", "detalhes": ex.errors(include_url=False)},
                          ensure_ascii=False, default=str)
    return json.dumps(funcao(**args.model_dump()), ensure_ascii=False)
```

O laço: `chamar_modelo` entra como parâmetro (API real ou roteiro); limite de rodadas numa dataclass `frozen`; cada
resultado volta como mensagem `role="tool"` com o `tool_call_id`.

**Pegadinhas**
- Sem `max_rodadas`, um modelo que pede ferramentas para sempre não termina **(V)**.
- Busca por nome exato: o modelo consultou `"tomate"`, a tabela tinha `"tomate italiano"` **(R)**.
- `float` para dinheiro acumula erro (`0.10 + 0.20 = 0.30000000000000004`) **(V)**.
- O resultado da ferramenta volta ao prompt: dado de fonte externa é entrada não confiável.
- `mensagem.model_dump(exclude_none=True)` ao reenviar a mensagem do assistente: endpoints compatíveis podem recusar campos `None`.

**Possibilidades**
- Chaves canônicas (`slug`) e tabela de sinônimos; ou ferramenta de busca que devolve candidatos.
- Ferramentas por rota (menor privilégio, [caso 05](05_roteamento_por_intencao.md)) e por perfil ([caso 07](07_permissoes_e_politicas.md)).
- Argumentos como união discriminada quando uma ferramenta tem modos.
