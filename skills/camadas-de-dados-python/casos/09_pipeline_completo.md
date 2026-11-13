# Caso 09 — Pipeline completo

[← SKILL.md](../SKILL.md) · [pegadinhas](../pegadinhas.md) · [referência](../referencia/ferramentas.md)

**Cenário:** juntar tudo: configuração do ambiente, entrada validada, classificação, rota, lista com contexto,
cache, log e testes.

```python
class Configuracoes(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COMPRAS_", env_file=find_dotenv(usecwd=True) or None,
                                      extra="ignore", validate_by_name=True)
    api_key: SecretStr = Field(validation_alias=AliasChoices("COMPRAS_API_KEY", "openai"))
    base_url: str = Field(default="https://api.openai.com/v1",
                          validation_alias=AliasChoices("COMPRAS_BASE_URL", "openai_base_url"))
    max_tentativas: int = Field(default=3, ge=1, le=5)

class Pedido(BaseModel):
    texto: str = Field(min_length=1, max_length=500)
    perfil: Perfil                       # da sessão
    porcoes: int = Field(default=2, ge=1, le=20)
    orcamento: Decimal | None = Field(default=None, gt=0)

def chave(pedido: Pedido) -> str:        # tudo que muda a resposta entra na chave
    normalizado = pedido.model_dump(mode="json") | {"texto": " ".join(pedido.texto.lower().split())}
    return hashlib.sha256(json.dumps(normalizado, sort_keys=True).encode()).hexdigest()[:16]
```

Eventos estruturados (`pedido`, `status`, `detalhe` já redigido) no console pelo logger e em JSONL; cliente simulado
com a mesma interface do `OpenAI(...)` para testes offline; trocar pelo cliente real é uma linha.

**Pegadinhas**
- Chave de cache só com o texto: um visitante recebe a resposta montada para um cliente **(V)**; cache sem TTL guarda preço velho.
- `str(SecretStr)` é `**********`; passar isso ao cliente dá erro de autenticação longe da causa **(V)**.
- `validation_alias` + `extra="ignore"`: `Configuracoes(api_key=...)` é ignorado em silêncio sem `validate_by_name=True` **(V)**.
- Redação por regex deixa passar formatos desconhecidos (`4111.1111...`, "ana arroba exemplo") **(V)**; o melhor é não registrar texto bruto.
- Testes com modelo simulado testam o encanamento, não a qualidade do modelo.

**Possibilidades**
- Avaliação com o cliente real medindo taxa de acerto, não passou/falhou.
- Idempotência com TTL ou invalidação por versão da tabela de preços.
