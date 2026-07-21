import typer

_PREFIX = "[mcnet]"


def info(message: str):
    typer.secho(f"{_PREFIX} {message}")


def ok(message: str):
    typer.secho(f"{_PREFIX} {message}", fg=typer.colors.GREEN)


def warn(message: str):
    typer.secho(f"{_PREFIX} {message}", fg=typer.colors.YELLOW)


def err(message: str):
    typer.secho(f"{_PREFIX} {message}", fg=typer.colors.RED, err=True)
