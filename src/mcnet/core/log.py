from rich.console import Console

_out = Console()
_err = Console(stderr=True)


def info(message: str) -> None:
    _out.print(message)


def ok(message: str) -> None:
    _out.print(message, style="green")


def warn(message: str) -> None:
    _err.print(f"warning: {message}", style="yellow")


def err(message: str) -> None:
    _err.print(f"error: {message}", style="red")
