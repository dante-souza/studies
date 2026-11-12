"""Contrato do básico e do intermediário, reunido para o avançado importar.

Igual ao `02_intermediario/contrato.py`, mais os enums criados no intermediário: `Ferramenta` (04) e `Intencao` (06).
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


class Ferramenta(StrEnum):  # 04
    CONSULTAR_PRECO = "consultar_preco"
    VERIFICAR_DESPENSA = "verificar_despensa"


class Intencao(StrEnum):  # 06
    RECEITA = "receita"
    PRECO = "preco"
    SUBSTITUICAO = "substituicao"
    FORA_DO_ESCOPO = "fora_do_escopo"
