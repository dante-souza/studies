"""Contrato construído no básico (notebooks 01–03), reunido num módulo para o intermediário importar.

Única mudança em relação ao 03: `Ingrediente.unidade` e `Ingrediente.categoria` já normalizam caixa e espaços
(a correção da pegadinha 1 do 03).
"""

import json
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


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


def extrair_json(texto: str) -> str:
    """Conteúdo entre a primeira '{' e a última '}'."""
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("nenhum objeto JSON na resposta")
    return texto[inicio:fim + 1]
