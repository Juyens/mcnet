from typing import Annotated

import typer

from mcnet.cli.handler import handle

app = typer.Typer(no_args_is_help=True)


@app.command()
@handle
def add(
    url: Annotated[str, typer.Argument(help="Modrinth or Hangar URL of the plugin")],
    names: Annotated[
        list[str],
        typer.Argument(help="Servers to add it to"),
    ],
):
    pass


@app.command()
def remove():
    pass


@app.command()
def show():
    pass


@app.command()
def search():
    pass
