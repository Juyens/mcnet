from typing import Annotated

import typer

from mcnet.cli import callbacks
from mcnet.core.loaders import ServerLoader

app = typer.Typer(no_args_is_help=True)


@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Name of the server")],
    version: Annotated[
        str,
        typer.Argument(help="Minecraft version", callback=callbacks.validate_version),
    ],
    loader: Annotated[
        ServerLoader, typer.Argument(help="Server software to run")
    ] = ServerLoader.PAPER,
):
    """Create a server in the current folder."""


@app.command()
def delete():
    pass


@app.command()
def edit():
    pass


@app.command()
def show():
    pass
