# Catálogo de pegadinhas

[← SKILL.md](SKILL.md)

Marcas: **(V)** verificada no estudo, com código executado; **(R)** observada em resposta real de LLM; sem marca =
comportamento conhecido da biblioteca, não testado no estudo. O detalhe de cada uma está no caso de uso correspondente
(pasta [`casos/`](casos/)).

Resumo para revisão rápida (detalhes nos casos acima).

| Área | Pegadinha | Remédio |
|---|---|---|
| Pydantic | `description` não é regra **(V)** | enum, restrição, validator |
| Pydantic | validators não aparecem no JSON Schema **(V)** | regra também no prompt/documentação |
| Pydantic | strict nativo: opcional vira obrigatório-nullable **(V)** | conte com `null` explícito |
| Pydantic | `model_copy(update=)` não valida **(V)** | revalidar |
| Pydantic | defaults não validados **(V)** | `validate_default=True` ou converter o default |
| Pydantic | vários `BeforeValidator`: ordem reversa **(V)** | um validator composto, ou ordem consciente |
| Pydantic | restrições antes do `AfterValidator` **(V)** | normalizar com `BeforeValidator` |
| Pydantic | `info.data` sem o campo que falhou (KeyError) **(V)** | `info.data.get(...)` |
| Pydantic | `exclude` ignora alias em silêncio **(V)** | usar nomes de campo |
| Pydantic | `model_validate(instância)` devolve a mesma **(V)** | `model_copy(deep=True)` se precisar cópia |
| Pydantic | `str(SecretStr)` é a máscara **(V)** | `get_secret_value()` só no uso |
| Pydantic | `validation_alias` + `extra="ignore"` engole o nome **(V)** | `validate_by_name=True` |
| Pydantic | 2.13.5: `_missing_` recebe `None` no JSON **(V)** | `BeforeValidator` para enum aberto |
| Pydantic | `use_enum_values` guarda `str`; `==` ainda funciona com StrEnum **(V)** | evitar, ou não usar `is`/`isinstance` |
| Pydantic | ordem de erros muda entre versões **(V)** | testar conteúdo |
| Pydantic + dataclass | `TypeAdapter` ignora extras **(V)** | `__pydantic_config__ = {"extra": "forbid"}` |
| dataclass | não valida **(V)** | Pydantic na borda |
| dataclass | default mutável **(V)** | `default_factory` |
| dataclass | frozen raso **(V)** | `MappingProxyType`, tuplas |
| dataclass | `slots=True` + `__init_subclass__` kwargs **(V)** | `ClassVar` |
| Enum | comparação exata **(V)** | normalizar na borda |
| Enum | `match` sem `case _` **(V)** | `case _: raise` ou `assert_never` |
| Enum | tabela sem cobertura **(V)** | `assert not set(E) - T.keys()` |
| Enum | renomear valor **(V)** | valor é contrato; renomeie só o nome |
| Enum | `Flag(0) in X` **(V)** | `is None` explícito |
| Enum + ORM | SQLAlchemy grava o nome por padrão **(V)** | `values_callable` |
| YAML | `no`/`off` → `False`, `3.10` → `3.1` **(V)** | aspas, `safe_load` |
| Números | float para dinheiro **(V)** | `Decimal(str(x))` |
| Números | `"1.5"` → `15` em parser BR **(V)** | regex estrita |
| LLM | JSON com cerca/texto **(R)** | `extrair_json` |
| LLM | quantidade não numérica **(R)** | decidir no contrato |
| LLM | confiança não calibrada **(R)** | avaliação com gabarito |
| LLM | nome não bate com a chave **(R)** | chaves canônicas, sinônimos |
| LLM | corte quebra pares de tool **(V)** | cortar por turno |
| Python | `assert` some com `-O` **(V)** | `if ...: raise` para regras |
| Python | variável do `except ... as ex` é apagada ao sair do bloco **(V)** | copiar o que precisa dentro do bloco |
| Python 3.11 | barra invertida dentro da expressão de f-string **(V)** | variável auxiliar |
| Notebook | duas classes com o mesmo nome confundem `pickle` **(V)** | nomes distintos por célula |
