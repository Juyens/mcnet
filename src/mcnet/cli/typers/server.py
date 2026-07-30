from pathlib import Path
from typing import Annotated

import typer

from mcnet import manifest
from mcnet.cli import callbacks
from mcnet.core import log, paths
from mcnet.core.loaders import ServerLoader
from mcnet.core.models import Manifest

app = typer.Typer(no_args_is_help=True)


@app.command()
def create(
    name: Annotated[
        str, typer.Argument(help="Name of the server", callback=callbacks.validate_name)
    ],
    version: Annotated[
        str,
        typer.Argument(help="Minecraft version", callback=callbacks.validate_version),
    ],
    loader: Annotated[
        ServerLoader,
        typer.Argument(help="Server software to run"),
    ] = ServerLoader.PAPER,
    port: Annotated[
        int,
        typer.Option(
            "--port", "-p", help="Port the server listens on", min=1024, max=65535
        ),
    ] = 25565,
):
    """Create a server in the current folder"""
    target = Path.cwd() / name

    if target.exists():
        log.err(f"{paths.display(target)} already exists")
        log.hint("pick another name, or remove the folder first")
        raise typer.Exit(code=1)

    target.mkdir(parents=True)

    server = Manifest(
        name=name,
        loader=loader.value,
        mc_version=version,
        port=port,
        plugins=[],
    )
    manifest_path = manifest.save(server, target)

    log.ok(f"created '{name}' ({loader.value} {version}) on port {port}")
    log.hint(f"manifest written to {paths.display(manifest_path)}")
    log.hint("run 'mcnet sync' to download the server jar")


@app.command()
def delete():
    pass


@app.command()
def edit():
    pass


@app.command()
def show():
    pass
