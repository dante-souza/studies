"""Portable, single-file pretty printer for terminals and notebooks, built on rich.

Python >= 3.10; one runtime dependency: rich. No application-specific code.

Public API:
    Prettifier, configure, get_default, show, show_json, show_panel, show_table,
    styled, view_file, rich_handler, TONES, run_selftest, main.

Conventions:
    * `show(...)` is a drop-in for print(): same arguments, colored output. In lines shaped
      like `label: value`, the label is highlighted; `SomethingError` / `SomethingException`
      are red; numbers, strings, None, booleans and reprs use rich's repr colors.
    * JSON detection: `show(text)` with a JSON object/array string, or `label: <JSON>`, is shown
      as JSON with key/value colors; on one line when it fits the width, indented otherwise.
      `show(text, detect_json=False)` prints the string as-is.
    * rich markup is OFF: "[text]" is printed literally, never interpreted as a style tag.
    * Semantic coloring: JSON string values under keys such as "status" or "level" get a tone
      (good / bad / warn / info / muted), shown as a colored badge so it never blends with JSON
      syntax colors. Rules are validated when passed, not when matched.
    * Inside Jupyter, output goes as ANSI text to stdout (one continuous stream per cell)
      instead of one HTML block per call. NO_COLOR=1 disables colors unless color="always".

To reuse: copy ONLY prettifier.py into another project and `pip install rich`.
Companion of logger_general.py (stdlib only): the logger records and persists; this module
displays. Neither imports the other.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import re
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

from rich import box
from rich.console import Console, Group
from rich.highlighter import JSONHighlighter, RegexHighlighter, ReprHighlighter
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

__version__ = "1.1.0"
__all__ = [
    "Prettifier", "configure", "get_default", "show", "show_json", "show_panel", "show_table",
    "styled", "view_file", "rich_handler", "TONES", "run_selftest", "main",
]

TONES = ("good", "bad", "warn", "info", "muted")

DEFAULT_THEME = Theme({
    "repr.label": "bold color(33)",
    "repr.bullet": "bold yellow",
    "repr.ok": "bold green",
    "repr.error": "bold red",
    "tone.good": "bold green",
    "tone.bad": "bold red",
    "tone.warn": "bold yellow",
    "tone.info": "bold color(33)",
    "tone.muted": "dim",
    # semantic values inside JSON: a badge (background), so they never blend with JSON syntax colors
    "badge.good": "bold black on color(34)",
    "badge.bad": "bold white on color(160)",
    "badge.warn": "bold black on color(178)",
    "badge.info": "bold white on color(33)",
    "badge.muted": "dim italic",
    "panel.title": "bold cyan",
    "log.time": "dim",
    "log.debug": "bold blue",
    "log.info": "bold green",
    "log.warning": "bold yellow",
    "log.error": "bold red",
    "log.critical": "bold white on red",
})

# Generic defaults; a value not listed here keeps the normal string color.
DEFAULT_SEMANTIC_KEYS = frozenset(("status", "state", "level", "severity", "result", "outcome", "resultado"))
DEFAULT_SEMANTIC_VALUES = {
    "ok": "good", "success": "good", "succeeded": "good", "passed": "good", "completed": "good", "done": "good",
    "authorized": "good", "sucesso": "good", "autorizado": "good", "concluido": "good",
    "warning": "warn", "warn": "warn", "pending": "warn", "denied": "warn", "blocked": "warn", "skipped": "warn",
    "negado": "warn", "pendente": "warn",
    "error": "bad", "failed": "bad", "failure": "bad", "critical": "bad", "fatal": "bad", "erro": "bad", "falha": "bad",
    "info": "info", "debug": "muted",
}

_JSON_STRING = re.compile(r'"(?:\\.|[^"\\])*"(?P<colon>\s*:)?')
_LABELED_JSON = re.compile(r"(?s)^(?P<label>[^\s{\[\"'#-][^\n:{}\[\]]{0,90}?): (?P<payload>[\[{].*)$")
_LOG_LEVEL = re.compile(r"\b(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\b")
_LOG_TIME = re.compile(r"^\s*\[?\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d(?:[.,]\d+)?\]?|^\s*\[?\d\d:\d\d:\d\d\]?")


class LabelHighlighter(RegexHighlighter):
    """rich's repr colors + `label:` at line start, `- ` bullets, a leading `ok` and *Error/*Exception names.

    Later patterns paint over earlier ones: the label gets a single color even if it contains numbers,
    and an error name stays red even when it is the label.
    """

    base_style = "repr."
    highlights = [
        *ReprHighlighter.highlights,
        r"(?m)^(?P<label>[^\s{\[\"'\n#-][^\n:]{0,90}?):(?= |$)",
        r"(?m)^(?P<bullet>- )",
        r"(?m)^(?P<ok>ok)\b",
        r"\b(?P<error>[A-Z]\w*(?:Error|Exception))\b",
    ]


def _check_tone(tone: str) -> str:
    if tone not in TONES:
        raise ValueError(f"unknown tone {tone!r}; use one of {', '.join(TONES)}")
    return tone


def _check_rules(rules: Mapping[str, Mapping[str, str]] | None) -> dict[str, dict[str, str]]:
    """Validate semantic rules up front and normalize them to casefolded keys and values."""
    checked: dict[str, dict[str, str]] = {}
    for key, mapping in (rules or {}).items():
        if not isinstance(mapping, Mapping):
            raise TypeError(f"semantic rule for {key!r} must map values to tones")
        checked[key.casefold()] = {str(value).casefold(): _check_tone(tone) for value, tone in mapping.items()}
    return checked


def _tone_for(key: str | None, value: str, rules: Mapping[str, Mapping[str, str]]) -> str | None:
    if key is None:
        return None
    key_low, value_low = key.casefold(), value.casefold()
    if key_low in rules and value_low in rules[key_low]:
        return rules[key_low][value_low]
    if key_low in DEFAULT_SEMANTIC_KEYS:
        return DEFAULT_SEMANTIC_VALUES.get(value_low)
    return None


def _semantic_spans(document: str, rules: Mapping[str, Mapping[str, str]]) -> Iterable[tuple[int, int, str]]:
    """Yield (start, end, tone) for string values whose key has a tone. Strings are consumed left to right,
    so escaped quotes inside strings never start a new token; a value counts only if it directly follows
    `"key":` (array items and later siblings do not)."""
    key: str | None = None
    key_end = 0
    for found in _JSON_STRING.finditer(document):
        if found.group("colon") is not None:
            key, key_end = json.loads(document[found.start():found.end() - len(found.group("colon"))]), found.end()
            continue
        if key is not None and not document[key_end:found.start()].strip():
            tone = _tone_for(key, json.loads(found.group(0)), rules)
            if tone:
                yield found.start(), found.end(), tone
        key = None


def _in_notebook() -> bool:
    return "ipykernel" in sys.modules


class Prettifier:
    """A configured rich Console plus the display helpers. Create one per output target, or use the
    module-level functions (they share a default instance, see `configure`)."""

    def __init__(
        self, *, color: str = "auto", width: int | None = None, file: TextIO | None = None,
        theme: Theme | None = None, highlighter: RegexHighlighter | None = None,
        notebook_ansi: bool = True, color_system: str | None = None,
    ) -> None:
        if color not in ("auto", "always", "never"):
            raise ValueError("color must be 'auto', 'always' or 'never'")
        notebook = notebook_ansi and _in_notebook() and file is None
        options: dict[str, Any] = {}
        if color == "never":
            options["color_system"] = None
        else:
            options["color_system"] = color_system or ("256" if notebook else "auto")
        if color == "always":
            options["force_terminal"] = True
            options["no_color"] = False
        elif notebook:
            options["force_terminal"] = True
        if notebook:
            options["force_jupyter"] = False
        self.console = Console(
            file=file, width=width or (110 if notebook else None), theme=theme or DEFAULT_THEME,
            highlighter=highlighter or LabelHighlighter(), markup=False, emoji=False, soft_wrap=False,
            **options,
        )

    # ---------------------------------------------------------------- printing
    def show(self, *objects: Any, sep: str = " ", end: str = "\n", detect_json: bool = True, **options: Any) -> None:
        """print() with colors. Non-string objects (models, dicts, lists) are pretty-printed.

        A single string that is a JSON object/array, or `label: <JSON object/array>`, is shown as JSON
        (see module docstring). Pass detect_json=False to print it as plain text.
        """
        if detect_json and len(objects) == 1 and isinstance(objects[0], str) and not options:
            rendered = self._json_from_text(objects[0])
            if rendered is not None:
                self.console.print(rendered, end=end)
                return
        self.console.print(*objects, sep=sep, end=end, **options)

    def _json_from_text(self, text: str) -> Any | None:
        """Renderable for a JSON string or `label: JSON` string; None when the text is not that."""
        stripped = text.strip()
        label, payload = None, stripped
        if stripped[:1] not in ("{", "["):
            found = _LABELED_JSON.match(stripped)
            if found is None:
                return None
            label, payload = found.group("label"), found.group("payload")
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, (dict, list)) or not data:
            return None
        rules = _check_rules(None)
        inline = self._json_text(data, indent=None, rules=rules, sort_keys=False)
        if len(inline.plain) + (len(label) + 2 if label else 0) <= self.console.width:
            return Text.assemble(Text(label, style="repr.label"), ": ", inline) if label else inline
        body = self._json_text(data, indent=2, rules=rules, sort_keys=False)
        return Group(Text.assemble(Text(label, style="repr.label"), ":"), body) if label else body

    @staticmethod
    def styled(text: Any, tone: str) -> Text:
        """Text with a semantic tone (good, bad, warn, info, muted), e.g. for a table cell."""
        return Text(str(text), style=f"tone.{_check_tone(tone)}")

    def _json_text(self, data: Any, *, indent: int | None, rules: Mapping[str, Mapping[str, str]],
                   sort_keys: bool) -> Text:
        if isinstance(data, (str, bytes)):
            data = json.loads(data)
        document = json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=sort_keys, default=str)
        text = Text(document)
        JSONHighlighter().highlight(text)
        for start, end, tone in _semantic_spans(document, rules):
            text.stylize(f"badge.{tone}", start, end)
        if indent is None:  # one long line: let it fold at the console width instead of being cropped
            text.no_wrap, text.overflow = False, "fold"
        else:
            text.no_wrap = True
        return text

    def show_json(self, data: Any, *, title: str | None = None, compact: bool = False, indent: int = 2,
                  semantic_rules: Mapping[str, Mapping[str, str]] | None = None, sort_keys: bool = False) -> None:
        """Highlighted JSON from a Python value or a JSON string, with semantic tones for status-like keys."""
        rules = _check_rules(semantic_rules)
        if title is not None:
            self.console.print(Text.assemble(Text(title, style="repr.label"), ":"))
        self.console.print(self._json_text(data, indent=None if compact else indent, rules=rules, sort_keys=sort_keys))

    def show_panel(self, text: str, *, title: str | None = None, detect_json: bool = True, compact: bool = False,
                   semantic_rules: Mapping[str, Mapping[str, str]] | None = None) -> None:
        """Wrapped text in a panel. With detect_json, a JSON document that ends the text (from the first '{'
        or '[' that starts valid JSON) is shown highlighted below the prose, e.g. a prompt with a schema."""
        rules = _check_rules(semantic_rules)
        parts: list[Any] = [Text(text)]
        if detect_json:
            for found in re.finditer(r"[\[{]", text):
                try:
                    data = json.loads(text[found.start():])
                except json.JSONDecodeError:
                    continue
                prose = text[:found.start()].rstrip()
                json_part = self._json_text(data, indent=None if compact else 2, rules=rules, sort_keys=False)
                parts = [Text(prose), json_part] if prose else [json_part]
                break
        self.console.print(Panel(Group(*parts), title=Text(title, style="panel.title") if title else None,
                                 title_align="left", box=box.ROUNDED, padding=(0, 1)))

    def show_table(self, columns: Sequence[str], rows: Iterable[Sequence[Any]], *, title: str | None = None) -> None:
        """Simple table. Text cells (see `styled`) keep their style; other cells are highlighted like `show`."""
        table = Table(*columns, title=title, title_justify="left", title_style="panel.title",
                      box=box.SIMPLE_HEAD, header_style="bold", highlight=True)
        for row in rows:
            table.add_row(*(cell if isinstance(cell, Text) else str(cell) for cell in row))
        self.console.print(table)

    # ---------------------------------------------------------------- files
    def _log_line(self, line: str) -> Text:
        text = Text(line.rstrip("\r\n"))
        stamp = _LOG_TIME.match(text.plain)
        if stamp:
            text.stylize("log.time", stamp.start(), stamp.end())
        level = _LOG_LEVEL.search(text.plain)
        if level:
            text.stylize(f"log.{level.group('level').lower()}", level.start(), level.end())
        return text

    def view_file(self, path: str | Path, *, kind: str = "auto", pretty: bool = False, headings: bool = True,
                  semantic_rules: Mapping[str, Mapping[str, str]] | None = None) -> int:
        """Display a .json, .jsonl/.ndjson or log file without modifying it.

        JSONL is streamed line by line; an invalid line is reported (warn tone) with its number and shown
        as-is, and reading continues. Returns the number of JSON records (or log lines) displayed.
        """
        if kind not in ("auto", "json", "jsonl", "log"):
            raise ValueError("kind must be auto, json, jsonl or log")
        rules = _check_rules(semantic_rules)
        source = Path(path)
        if kind == "auto":
            suffix = source.suffix.lower()
            kind = "json" if suffix == ".json" else "jsonl" if suffix in (".jsonl", ".ndjson") else "log"
        if kind == "json":
            with source.open(encoding="utf-8") as handle:
                data = json.load(handle)
            self.console.print(self._json_text(data, indent=2, rules=rules, sort_keys=False))
            return 1
        count = 0
        with source.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if kind == "log":
                    self.console.print(self._log_line(line))
                    count += 1
                    continue
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    self.console.print(self.styled(f"invalid JSON on line {number} of {source.name}: {exc.msg}", "warn"))
                    self.console.print(Text(line.rstrip("\r\n"), style="tone.muted"))
                    continue
                count += 1
                if pretty and headings:
                    self.console.print(self._heading(data, count, rules))
                self.console.print(self._json_text(data, indent=2 if pretty else None, rules=rules, sort_keys=False))
        return count

    @staticmethod
    def _heading(data: Any, index: int, rules: Mapping[str, Mapping[str, str]]) -> Text:
        label = Text(f"record {index:04d}", style="bold")
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    tone = _tone_for(key, value, rules)
                    if tone:
                        label.append(f"  {key}: ")
                        label.append(value, style=f"tone.{tone}")
                        break
        return label

    # ---------------------------------------------------------------- logging
    def rich_handler(self, level: int | str = logging.NOTSET, **options: Any) -> logging.Handler:
        """A logging.Handler that writes through this console (rich's RichHandler, markup off, no file paths)."""
        from rich.logging import RichHandler

        settings = {"show_path": False, "markup": False, "rich_tracebacks": True, "log_time_format": "%H:%M:%S"}
        settings.update(options)
        return RichHandler(level=level, console=self.console, **settings)


# ---------------------------------------------------------------- module-level shortcuts
_default: Prettifier | None = None


def configure(**options: Any) -> Prettifier:
    """Replace the default instance used by the module-level functions. Same options as Prettifier()."""
    global _default
    _default = Prettifier(**options)
    return _default


def get_default() -> Prettifier:
    global _default
    if _default is None:
        _default = Prettifier()
    return _default


def show(*objects: Any, **options: Any) -> None:
    get_default().show(*objects, **options)


def show_json(data: Any, **options: Any) -> None:
    get_default().show_json(data, **options)


def show_panel(text: str, **options: Any) -> None:
    get_default().show_panel(text, **options)


def show_table(columns: Sequence[str], rows: Iterable[Sequence[Any]], **options: Any) -> None:
    get_default().show_table(columns, rows, **options)


def styled(text: Any, tone: str) -> Text:
    return Prettifier.styled(text, tone)


def view_file(path: str | Path, **options: Any) -> int:
    return get_default().view_file(path, **options)


def rich_handler(level: int | str = logging.NOTSET, **options: Any) -> logging.Handler:
    return get_default().rich_handler(level, **options)


# ---------------------------------------------------------------- demo, selftest, CLI
def run_demo(*, color: str = "always") -> None:
    """Executable tour of the helpers, without external services."""
    p = Prettifier(color=color)
    p.show("count: 3")
    p.show("ratio: 0.25 | name: 'ação' | missing: None | enabled: True")
    p.show("ValueError: 'G' is not a valid Unit")
    p.show("[section] markup is printed literally")
    p.show('order: {"id": 7, "items": [{"sku": "A-1", "qty": 2}, {"sku": "B-9", "qty": 1}], "status": "pending", '
           '"note": "long JSON strings are indented when they do not fit the width"}')
    p.show_json({"id": 1, "status": "success", "detail": {"retry": False, "note": None}}, title="record")
    p.show_panel('Answer ONLY with JSON that follows this schema:\n{"type": "object", "properties": {"n": {"type": "integer"}}}',
                 title="prompt")
    p.show_table(["step", "result"], [["parse", p.styled("ok", "good")], ["validate", p.styled("failed", "bad")]],
                 title="checks")
    with tempfile.TemporaryDirectory(prefix="prettifier-") as folder:
        events = Path(folder) / "events.jsonl"
        events.write_text('{"status": "success"}\n{"status": "denied"}\nnot json\n', encoding="utf-8")
        p.view_file(events)


def run_selftest(*, color: str = "always") -> None:
    """Fast, assertion-based checks of formatting, safety and file handling."""
    def capture(colored: bool) -> tuple[Prettifier, io.StringIO]:
        buffer = io.StringIO()
        return Prettifier(color="always" if colored else "never", width=100, file=buffer), buffer

    plain, out = capture(False)
    plain.show("label: [bold]x[/bold] :ok:")
    assert out.getvalue() == "label: [bold]x[/bold] :ok:\n", out.getvalue()      # markup and emoji off
    plain.show_json({"status": "denied", "note": "ação", "n": 1})
    assert json.loads(out.getvalue().split("\n", 1)[1]) == {"status": "denied", "note": "ação", "n": 1}

    colored, out = capture(True)
    colored.show("count: 3")
    assert "\x1b[" in out.getvalue() and "count" in out.getvalue()
    spans = list(_semantic_spans('{"status": "denied", "items": ["denied"], "note": "x \\"status\\": \\"ok\\""}',
                                 _check_rules(None)))
    assert [tone for *_, tone in spans] == ["warn"], spans                        # only the real status value
    assert list(_semantic_spans('{"etapa": "falhou"}', _check_rules({"ETAPA": {"FALHOU": "bad"}})))
    for bad_call in (lambda: styled("x", "loud"), lambda: _check_rules({"status": {"x": "loud"}})):
        try:
            bad_call()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid tone accepted")

    plain, out = capture(False)
    long_json = json.dumps([{"ingredient": f"item {i}", "amount": "250 grams"} for i in range(6)])
    plain.show(long_json)                                                        # long: indented
    assert out.getvalue().startswith('[\n  {\n    "ingredient": "item 0"'), out.getvalue()[:60]
    out.seek(0), out.truncate()
    plain.show(f"resposta: {long_json}")                                         # label + indented JSON
    assert out.getvalue().startswith('resposta:\n[\n  {'), out.getvalue()[:40]
    out.seek(0), out.truncate()
    for kept in ('sizes: [1, 2, 3]', 'short: {"a":1}', "repr: {'a': 1}", "n: 5", "[x] not json"):
        plain.show(kept)                                                          # fits or is not JSON: one line
    assert out.getvalue().splitlines() == ["sizes: [1, 2, 3]", 'short: {"a": 1}', "repr: {'a': 1}", "n: 5",
                                           "[x] not json"], out.getvalue()
    out.seek(0), out.truncate()
    plain.show(long_json, detect_json=False)
    assert out.getvalue().startswith('[{"ingredient"'), out.getvalue()[:30]
    out.seek(0), out.truncate()
    plain.show_panel("Use this schema:\n" + json.dumps({"a": [1, 2]}), title="prompt", compact=True)
    assert "Use this schema:" in out.getvalue() and '{"a": [1, 2]}' in out.getvalue()
    plain.show_json({"long": "y" * 250}, compact=True)
    assert out.getvalue().count("y") >= 250                                      # folded, not cropped

    with tempfile.TemporaryDirectory(prefix="prettifier-test-") as folder:
        path = Path(folder) / "events.jsonl"
        path.write_text('{"status": "success"}\n\nnot json\n{"status": "failed"}\n', encoding="utf-8")
        original = path.read_bytes()
        plain, out = capture(False)
        assert plain.view_file(path, pretty=True) == 2
        assert "invalid JSON on line 3" in out.getvalue() and "record 0002  status: failed" in out.getvalue()
        assert path.read_bytes() == original
        log = Path(folder) / "app.log"
        log.write_text("2026-01-01 10:00:00 | WARNING  | disk almost full\n", encoding="utf-8")
        assert plain.view_file(log) == 1

    colored, out = capture(True)
    logger = logging.Logger("prettifier-selftest")
    logger.addHandler(colored.rich_handler())
    logger.warning("handler works")
    assert "handler works" in out.getvalue() and "WARNING" in out.getvalue()
    Prettifier(color=color).show("ok selftest passed: markup off, JSON detection, semantic tones, panels, tables, files, handler")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Portable rich-based prettifier (JSON, JSONL, logs, tables)")
    parser.add_argument("--version", action="version", version=__version__)
    subs = parser.add_subparsers(dest="command", required=True)
    for action in ("demo", "selftest"):
        sub = subs.add_parser(action, help=f"Run {action} without external services")
        sub.add_argument("--color", choices=("auto", "always", "never"), default="always")
    viewer = subs.add_parser("view", help="Display an existing JSON, JSONL, NDJSON or log file")
    viewer.add_argument("file")
    viewer.add_argument("--kind", choices=("auto", "json", "jsonl", "log"), default="auto")
    viewer.add_argument("--pretty", action="store_true", help="indent each JSONL record")
    viewer.add_argument("--no-headings", action="store_true")
    viewer.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            run_demo(color=args.color)
        elif args.command == "selftest":
            run_selftest(color=args.color)
        else:
            Prettifier(color=args.color).view_file(args.file, kind=args.kind, pretty=args.pretty,
                                                   headings=not args.no_headings)
    except (OSError, ValueError, TypeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
