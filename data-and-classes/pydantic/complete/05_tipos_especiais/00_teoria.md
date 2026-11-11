# Seção 5 — Tipos especializados do Pydantic: teoria

> Notebooks: [`01`](01_links_da_documentacao.ipynb) links · [`02`](02_positiveint.ipynb) `PositiveInt` · [`03`](03_listas_com_restricoes.ipynb)
> listas com restrições · [`04`](04_uuid.ipynb) UUID · [`05`](05_tipos_de_data.ipynb) datas · [`06`](06_tipos_de_rede.ipynb) rede ·
> projeto: [`07`](07_projeto.ipynb) · [`08`](08_projeto_solucao_instrutor.ipynb) · [`09`](09_projeto_solucao_comentada.ipynb)

## Ideia central

Antes de escrever um validador, procure um **tipo pronto**: o Pydantic já traz tipos com regra embutida, que também aparecem no
JSON Schema.

| família | exemplos | regra |
|---|---|---|
| números | `PositiveInt`, `NonNegativeFloat`, `conint(...)` | sinal / faixa |
| coleções | `conlist(int, min_length=1)` (hoje, prefira `Annotated[list[int], Field(min_length=1)]`) | tamanho |
| UUID | `UUID1`, `UUID4`, … | formato **e versão** do UUID |
| datas | `PastDate`, `FutureDate`, `PastDatetime`, `AwareDatetime`, `NaiveDatetime` | relação com "agora" / presença de fuso |
| rede | `HttpUrl`, `AnyUrl`, `EmailStr`, `NameEmail`, `IPvAnyAddress` | formato (e normalização) |

```
tipo especializado = tipo base + restrição  →  validação + JSON Schema de graça
         PositiveInt = int  +  gt=0
```

## Pegadinhas verificadas

- `HttpUrl` **normaliza** a URL (ex.: acrescenta `/` final ao host) — o valor salvo não é a string recebida.
- `PastDatetime` com datetime *naive* compara contra a hora **local** da máquina. O notebook fixa o fuso (`TZ=America/Phoenix`, como o
  instrutor) para o resultado ser reprodutível em qualquer servidor.
- `EmailStr` exige o pacote `email-validator`.

## Projeto

Acrescentar `id_: UUID4 | None` como **primeiro** campo, lido e serializado como `id` (default `None` por enquanto). A solução comentada
dispensa o `Field(alias="id")` (o `make_alias` já gera `id`) e testa posição do campo, UUID inválido, UUID de **outra versão**, JSON e
atribuição.
