"""Contrato do básico e do intermediário, reunido para o avançado importar.

Igual ao `02_intermediario/contrato.py`, mais os enums criados no intermediário: `Ferramenta` (04) e `Intencao` (06).
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


class Ferramenta(StrEnum):  # 04
    CONSULTAR_PRECO = "consultar_preco"
    VERIFICAR_DESPENSA = "verificar_despensa"


class Intencao(StrEnum):  # 06
    RECEITA = "receita"
    PRECO = "preco"
    SUBSTITUICAO = "substituicao"
    FORA_DO_ESCOPO = "fora_do_escopo"
