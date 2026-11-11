"""Funções referenciadas POR NOME nas especificações de modelos (notebook 05).

A regra de negócio fica em código Python, revisável e testável; o arquivo de especificação só aponta qual usar.

- NORMALIZERS: rodam ANTES da validação do tipo e das restrições (BeforeValidator) — recebem o dado cru.
- VALIDATORS:  rodam DEPOIS (AfterValidator) — recebem o valor já tipado e já dentro das restrições.
"""
from collections.abc import Callable
from typing import Any


def strip_title(value: Any) -> Any:
    """'  bmw   motors ' -> 'Bmw Motors'."""
    return " ".join(value.split()).title() if isinstance(value, str) else value


def upper(value: Any) -> Any:
    return value.upper() if isinstance(value, str) else value


def no_digits(value: str) -> str:
    if any(ch.isdigit() for ch in value):
        raise ValueError("não pode conter dígitos")
    return value


NORMALIZERS: dict[str, Callable[[Any], Any]] = {"strip_title": strip_title, "upper": upper}
VALIDATORS: dict[str, Callable[[Any], Any]] = {"no_digits": no_digits}
