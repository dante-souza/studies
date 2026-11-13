"""Contrato construído no básico (notebooks 01–03), reunido num módulo para o intermediário importar.

Mudanças em relação ao básico: `Ingrediente.unidade` e `Ingrediente.categoria` já normalizam caixa e espaços
(a correção da pegadinha 1 do 03), e a borda de texto do LLM (`extrair_json` por decodificação e o tipo de borda
`saida_llm`) vem da pegadinha 2 do 02.
"""

import json
from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, Json, TypeAdapter


class Unidade(StrEnum):
    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    UN = "un"


class Categoria(StrEnum):
    HORTIFRUTI = "hortifruti"
    LATICINIOS = "laticinios"
    CARNES = "carnes"
    MERCEARIA = "mercearia"
    PADARIA = "padaria"


def normalizar_texto(valor):
    return valor.strip().lower() if isinstance(valor, str) else valor


class Ingrediente(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str
    quantidade: float = Field(gt=0)
    unidade: Annotated[Unidade, BeforeValidator(normalizar_texto)]
    categoria: Annotated[Categoria, BeforeValidator(normalizar_texto)]


class ListaDeCompras(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prato: str
    porcoes: int = Field(gt=0)
    ingredientes: list[Ingrediente]


def prompt_com_schema(instrucao: str, modelo: type[BaseModel]) -> str:
    return (
        f"{instrucao}\n"
        "Responda SOMENTE com um JSON válido que siga este JSON Schema:\n"
        f"{json.dumps(modelo.model_json_schema(), ensure_ascii=False)}"
    )


def extrair_json(texto):
    """Primeiro JSON (objeto ou lista) decodificável no texto, devolvido como texto, sem nada em volta.

    Decodifica a partir de cada '{' ou '[' (json.JSONDecoder.raw_decode) em vez de recortar da primeira '{' até a
    última '}': cercas, prosa com chaves e listas soltas não enganam. O que não é texto passa adiante sem mudança.
    """
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
    """Tipo de borda: texto do LLM -> objeto validado. É o único lugar da aplicação onde existe texto.

    Json[modelo] valida o texto JSON contra o modelo; o BeforeValidator tira antes o que vem em volta.
    "Sem JSON" vira ValidationError como qualquer outro erro. Uso: saida_llm(Modelo).validate_python(texto, context=...).
    """
    return TypeAdapter(Annotated[Json[modelo], BeforeValidator(extrair_json)])
