# Pydantic V2: Essentials — material do curso traduzido, revisado e resolvido

Material do curso **[Pydantic V2: Essentials](https://www.udemy.com/course/pydantic/)**, de **Fred Baptiste**
([MathByte Academy](https://www.youtube.com/@mathbyteacademy)), distribuído sob **GNU AGPL-3.0** — a licença original está em
[`LICENSE`](LICENSE) e vale para este diretório. Esta pasta é uma obra derivada:

- **todas as aulas traduzidas para português**, com nomes de arquivo em português;
- **reexecutadas** no Pydantic 2.13.5 / Python 3.13 (o curso foi gravado no 2.5) — todas as células rodam sem erro;
- saídas no formato `expressão: valor` (f-strings, um valor por linha), como no resto do repositório;
- **📝 notas de revisão** onde o curso diverge do Pydantic atual ou tem bugs — sempre com a prova executada e o código corrigido;
- **todos os projetos resolvidos**: para cada seção há o enunciado, a solução do instrutor (traduzida e revisada) e uma
  **solução comentada** própria, com testes extras e comparação com a do instrutor;
- um **`00_teoria.md`** por seção, com o resumo conceitual e as divergências encontradas.
- um **`99_pegadinhas_e_caveats`** por seção: as notas de revisão da seção num quadro e pegadinhas novas, com demonstração.

## Como rodar

```bash
pip install -r requirements.txt
jupyter lab
```

Cada notebook roda a partir da própria pasta (os arquivos de dados ficam ao lado). Nenhum notebook depende de rede: o da API REST
(seção 12) tenta a chamada real e, se não conseguir, usa respostas gravadas.

## Mapa

| pasta | seção original | aulas | projeto |
|---|---|---|---|
| [`02_basico`](02_basico/00_teoria.md) | 02 - Basics | criação, (des)serialização, coerção, obrigatório/opcional/anulável, `model_fields`, JSON Schema | ✅ |
| [`03_configuracao_do_modelo`](03_configuracao_do_modelo/00_teoria.md) | 03 - Model Configuration | extras, strict/lax, defaults, atribuição, mutabilidade, strings, enums | ✅ |
| [`04_aliases_serializacao_desserializacao`](04_aliases_serializacao_desserializacao/00_teoria.md) | 04 - Field Aliasing, Serialization and Deserialization | aliases, geradores de alias, aliases de validação/serialização, serializadores | ✅ |
| [`05_tipos_especiais`](05_tipos_especiais/00_teoria.md) | 05 - Specialized Pydantic Types | `PositiveInt`, listas com restrição, UUID, datas, rede | ✅ |
| [`06_recursos_do_field`](06_recursos_do_field/00_teoria.md) | 06 - Additional Field Features | restrições numéricas e de string, default factories, configurações por campo | ✅ |
| [`07_tipos_annotated`](07_tipos_annotated/00_teoria.md) | 07 - Annotated Types | `Annotated`, `TypeVar`, `StringConstraints` | ✅ |
| [`08_validadores_customizados`](08_validadores_customizados/00_teoria.md) | 08 - Custom Validators | *before*/*after*, validadores no tipo, validação entre campos | ✅ |
| [`09_propriedades_e_computed_fields`](09_propriedades_e_computed_fields/00_teoria.md) | 09 - Properties and Computed Fields | propriedades, `@computed_field`, cache | ✅ |
| [`10_serializadores_customizados_annotated`](10_serializadores_customizados_annotated/00_teoria.md) | 10 - Custom Serializers using Annotated Types | `PlainSerializer`, `WrapSerializer`, `when_used` | ✅ |
| [`11_modelos_complexos`](11_modelos_complexos/00_teoria.md) | 11 - Complex Models | composição, herança | ✅ |
| [`12_aplicacoes`](12_aplicacoes/00_teoria.md) | 12 - Applications | API REST, CSV, `@validate_call`, `datamodel-codegen` | — (não há projeto) |

Em cada pasta de projeto: `NN_projeto` (enunciado) → `NN_projeto_solucao_instrutor` → `NN_projeto_solucao_comentada`. A seção 11 tem
também a `06_projeto_solucao_final_instrutor` (a mesma solução, reorganizada). Os nomes seguem a ordem dos arquivos originais
(`03 - Strict and Lax Type Coercion` → `03_coercao_strict_e_lax`, etc.).

## O projeto `Automobile`, seção a seção

O projeto cresce a cada seção; a solução comentada de cada uma parte da anterior.

| seção | o que entra | principal achado na revisão |
|---|---|---|
| 2 | campos obrigatórios, opcionais e anuláveis | tentativa original: `str = None` rejeita `null` explícito |
| 3 | `ConfigDict`, `Enum` | tentativa original: `type_` declarado duas vezes |
| 4 | aliases e serializador de data | tentativa original: `alias=` em vez de `validation_alias` → testes `by_alias` falham; ida e volta pelo JSON quebrada |
| 5 | `id_: UUID4` | — |
| 6 | restrições, `default_factory` | — |
| 7 | `BoundedString`, `BoundedList[T]` | instrutor: `id_` volta a ser anulável (regressão) |
| 8 | `Country`, validação entre datas | instrutor: `TypeError` para qualquer carro sem data de registro |
| 9 | campo calculado cacheado | instrutor: `KeyError` sem país; cache desatualizado |
| 10 | `CustomDate` | instrutor: o tipo não lê o próprio formato de saída |
| 11 | `CamelBaseModel` + `RegistrationCountry` | bugs da seção 9 migram para o submodelo; resolvidos com `frozen=True` |

## Suas tentativas originais

Os arquivos que você havia feito (`My_Project` das seções 2, 3 e 4) estão preservados **sem alteração** em
[`tentativas_originais/`](tentativas_originais/). A revisão de cada um está na seção "Revisão da sua tentativa" da solução comentada
correspondente.

## Achados de revisão (resumo)

Divergências de versão (2.5 → 2.13): `model_fields` pela instância depreciado; strict rejeita tupla→lista também; `AliasChoices` respeita
a ordem da lista, não a dos dados; `AliasGenerator` já suporta serialização; `populate_by_name` → `validate_by_name`/`validate_by_alias`;
`model_dump_json` não usa `json.dumps`; defaults mutáveis são copiados.

Bugs no material: células de código com prosa (`SyntaxError`); `user_list or []`; exemplo "JSON" que gerava `dict`; `Point2D.y` com `gt=0`
rejeitando o próprio exemplo; `query_id: uuid4` (função como tipo); validador *after* sem tratar `None`; `raise_for_status` sem
parênteses; mensagem de erro sem "not"; versão "Python puro" que quebra com o tipo que declara aceitar; `pattern` sem âncora.

Cada item está demonstrado (com saída) no notebook onde aparece.
