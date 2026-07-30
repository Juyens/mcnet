from rich.console import Console
from rich.text import Text

_out = Console()
_err = Console(stderr=True)

# Lines up with the text after a one-character symbol plus its space.
_INDENT = "  "


def _write(console: Console, symbol: str, style: str, message: str) -> None:
    line = Text(symbol, style=style)
    line.append(" ")
    line.append(message)
    console.print(line)


def info(message: str) -> None:
    _out.print(Text(message))


def hint(message: str) -> None:
    _err.print(Text(_INDENT + message, style="dim"))


def ok(message: str) -> None:
    _write(_out, "+", "bold green", message)


def warn(message: str) -> None:
    _write(_err, "!", "bold yellow", message)


def err(message: str) -> None:
    _write(_err, "x", "bold red", message)
