# Seção 6 — Recursos adicionais do `Field`: teoria

> Notebooks: [`02`](02_restricoes_numericas.ipynb) restrições numéricas · [`03`](03_restricoes_de_string.ipynb) restrições de string ·
> [`04`](04_default_factories.ipynb) default factories · [`05`](05_configuracoes_adicionais_de_campo.ipynb) configurações adicionais ·
> projeto: [`06`](06_projeto.ipynb) · [`07`](07_projeto_solucao_instrutor.ipynb) · [`08`](08_projeto_solucao_comentada.ipynb)

## Ideia central

`Field(...)` é onde a regra de **um campo** mora: restrições, default, alias, documentação, visibilidade. Se a seção 3 é a política do
modelo, `Field` é a exceção/precisão por campo.

| grupo | parâmetros | observação |
|---|---|---|
| números (e datas) | `gt`, `ge`, `lt`, `le`, `multiple_of` | funcionam com qualquer tipo comparável, inclusive `date` |
| strings | `min_length`, `max_length`, `pattern` | `pattern` é **busca**, não *match* completo — ancore com `^...$` (ver seção 12) |
| defaults | `default`, `default_factory` | `default_factory` para valores que devem ser **novos** a cada instância (`uuid4`, `datetime.now`) |
| documentação | `description` (também `title`, `examples`) | vão para o JSON Schema |
| comportamento | `frozen`, `exclude`, `strict`, `validate_default`, `repr` | as mesmas chaves da seção 3, agora **por campo**; `repr=False` é usado na seção 9 |

## Defaults mutáveis

```python
class M(BaseModel):
    tags: list[str] = []      # seguro no Pydantic: o default é COPIADO por instância
```

Diferente de uma função Python comum, o Pydantic copia (*deep copy*) o default mutável para cada instância. O curso dizia que ele era
"substituído por uma factory"; o efeito é o mesmo, mas o mecanismo documentado é a cópia — o notebook prova que as listas são
independentes. Para valores que precisam ser **diferentes** (UUID, timestamp), aí sim `default_factory`.

## Projeto

Data mínima de fabricação (`ge=date(1980, 1, 1)`), portas `ge=2, le=4, multiple_of=2`, e `id_` **não anulável** com
`default_factory=uuid4`. A solução comentada testa as fronteiras exatas (1979-12-31 × 1980-01-01; 0 a 6 portas) e a unicidade em
1000 instâncias, conferindo a versão do UUID.
