from rich.console import Console
from rich.text import Text

from mcnet.core.theme import THEME, McnetHighlighter

_out = Console(highlighter=McnetHighlighter(), theme=THEME, markup=False)
_err = Console(stderr=True, highlighter=McnetHighlighter(), theme=THEME, markup=False)


_INDENT = "  "


def _write(console: Console, symbol: str, color: str, message: str) -> None:
    console.print(Text(symbol, style=f"bold {color}"), message, style=color)


def info(message: str) -> None:
    _out.print(message)


def detail(message: str) -> None:
    _out.print(_INDENT + message)


def hint(message: str) -> None:
    _write(_err, ">", "bright_black", message)


def ok(message: str) -> None:
    _write(_out, "+", "green", message)


def warn(message: str) -> None:
    _write(_err, "!", "yellow", message)


def err(message: str) -> None:
    _write(_err, "x", "red", message)
