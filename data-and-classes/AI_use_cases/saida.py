"""Saída formatada da trilha AI_use_cases.

Duas responsabilidades, separadas de propósito:

* **Resultados** (o que o notebook quer mostrar) → `rich`: cores no padrão `rótulo: valor`, JSON destacado,
  prompts em painel com quebra de linha, tabelas.
* **Eventos de execução** (rodadas de ferramenta, tentativas, negações, cache) → `GeneralLogger` do
  `logger_general.py`, usado sem modificações: linha com horário e nível, colorida pelo nível.

As cores saem como ANSI na saída padrão: aparecem no Jupyter, no VS Code e no terminal. `NO_COLOR=1` desliga tudo.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from typing import Any, Iterable, Sequence

from rich import box
from rich.console import Console, Group
from rich.highlighter import ReprHighlighter
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from logger_general import GeneralLogger

__all__ = ["console", "mostrar", "mostrar_json", "mostrar_prompt", "tabela", "marcado", "registrador"]


class Destaque(ReprHighlighter):
    """O destaque padrão do rich (números, strings, None, True/False, reprs) + rótulos e erros.

    A ordem importa: padrões posteriores pintam por cima dos anteriores. O rótulo vem depois dos padrões do rich
    (fica com uma cor só) e o erro vem por último (vermelho mesmo quando ocupa a posição de rótulo).
    """

    highlights = [
        *ReprHighlighter.highlights,
        r"(?m)^(?P<rotulo>[^\s{\[\"'\n#-][^\n:]{0,90}?):(?= |$)",
        r"(?m)^(?P<item>- )",
        r"(?m)^(?P<ok>ok) ",
        r"\b(?P<erro>[A-Z]\w*(?:Error|Exception))\b",
    ]


TEMA = Theme({
    "repr.rotulo": "bold color(33)",
    "repr.item": "bold yellow",
    "repr.ok": "bold green",
    "repr.erro": "bold red",
    "titulo.painel": "bold cyan",
    "tom.bom": "bold green",
    "tom.ruim": "bold red",
    "tom.alerta": "bold yellow",
})

console = Console(
    highlighter=Destaque(),
    theme=TEMA,
    markup=False,                # "[hortifruti]" é texto, não marcação do rich
    emoji=False,                 # ":ok:" é texto, não emoji
    force_terminal=True,         # ANSI também dentro do kernel do Jupyter
    force_jupyter=False,         # uma saída de texto contínua, em vez de um bloco HTML por print
    color_system="256",
    width=110 if "ipykernel" in sys.modules else None,
    soft_wrap=False,
)


def mostrar(*objetos: Any, **opcoes: Any) -> None:
    """Substituto do print: mesmo uso, com cores. Objetos (modelos Pydantic, dicts) saem com pretty-print."""
    console.print(*objetos, **opcoes)


def _rotulo(texto: str) -> Text:
    return Text(texto, style="repr.rotulo")


def mostrar_json(rotulo: str, dado: Any) -> None:
    """JSON destacado e indentado. Aceita texto JSON ou objeto Python serializável."""
    corpo = JSON(dado) if isinstance(dado, str) else JSON.from_data(dado, ensure_ascii=False, default=str)
    console.print(Text.assemble(_rotulo(rotulo), ":"))
    console.print(corpo)


def mostrar_prompt(rotulo: str, texto: str, *, compacto: bool = False) -> None:
    """Prompt num painel: a instrução com quebra de linha e, se houver, o JSON Schema destacado à parte.

    `compacto=True` mostra o schema sem indentação (quebrado na largura do painel), para schemas grandes.
    """
    inicio = texto.find("{")
    partes: list[Any] = [Text(texto if inicio == -1 else texto[:inicio].rstrip())]
    if inicio != -1:
        try:
            dado = json.loads(texto[inicio:])
            corpo = JSON.from_data(dado, ensure_ascii=False, indent=None if compacto else 2)
            if compacto:  # o JSON do rich não quebra linha por padrão; compacto precisa quebrar para caber
                corpo.text.no_wrap, corpo.text.overflow = False, "fold"
            partes.append(corpo)
        except json.JSONDecodeError:
            partes = [Text(texto)]
    console.print(Panel(Group(*partes), title=Text(rotulo, style="titulo.painel"), title_align="left",
                        box=box.ROUNDED, padding=(0, 1)))


def marcado(texto: Any, tom: str) -> Text:
    """Texto com cor de significado, para células de tabela: tom = 'bom', 'ruim' ou 'alerta'."""
    if tom not in ("bom", "ruim", "alerta"):
        raise ValueError(f"tom inválido: {tom!r}")
    return Text(str(texto), style=f"tom.{tom}")


def tabela(colunas: Sequence[str], linhas: Iterable[Sequence[Any]], *, titulo: str | None = None) -> None:
    """Tabela simples; cada célula passa pelo mesmo destaque do `mostrar`."""
    t = Table(*colunas, title=titulo, title_justify="left", title_style="titulo.painel",
              box=box.SIMPLE_HEAD, header_style="bold", highlight=True)
    for linha in linhas:
        t.add_row(*(c if isinstance(c, Text) else str(c) for c in linha))
    console.print(t)


@lru_cache(maxsize=None)
def registrador(nome: str = "trilha", nivel: str = "INFO") -> GeneralLogger:
    """GeneralLogger na saída padrão (no Jupyter, stderr vira bloco vermelho). Um por nome, reaproveitado."""
    return GeneralLogger(name=nome, level=nivel, stream=sys.stdout, color="auto")
