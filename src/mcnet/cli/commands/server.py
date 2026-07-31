from typing import Annotated

import typer

from mcnet.cli import callbacks
from mcnet.cli.handler import handle
from mcnet.cli.render import changes, log
from mcnet.domain.loaders import ServerLoader
from mcnet.errors import McnetError
from mcnet.services import servers
from mcnet.storage import paths

app = typer.Typer(no_args_is_help=True)


def _confirm(name: str, refusal: str) -> None:
    if typer.prompt(f"Type '{name}' to confirm") != name:
        raise McnetError(f"name does not match, {refusal}")


@app.command()
@handle
def create(
    name: Annotated[
        str, typer.Argument(help="Name of the server", callback=callbacks.validate_name)
    ],
    mc_version: Annotated[
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
    manifest_path = servers.create(
        name, loader=loader.value, mc_version=mc_version, port=port
    )

    log.ok(f"created '{name}' ({loader.value} {mc_version}) on port {port}")
    log.hint(f"manifest written to {paths.display(manifest_path)}")
    log.hint("run 'mcnet sync' to download the server jar")


@app.command()
@handle
def edit(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the server to edit", callback=callbacks.validate_name
        ),
    ],
    loader: Annotated[
        ServerLoader | None,
        typer.Option("--loader", "-l", help="Server software to run"),
    ] = None,
    mc_version: Annotated[
        str | None,
        typer.Option(
            "--version",
            "-v",
            help="Minecraft version",
            callback=callbacks.validate_version,
        ),
    ] = None,
    port: Annotated[
        int | None,
        typer.Option(
            "--port", "-p", help="Port the server listens on", min=1024, max=65535
        ),
    ] = None,
):
    """Change the settings of a server"""
    folder = servers.locate(name)
    result = servers.edit(
        folder,
        loader=None if loader is None else loader.value,
        mc_version=mc_version,
        port=port,
    )

    if not result.applied and not result.unchanged:
        log.warn("nothing to change")
        raise typer.Exit()

    if result.unchanged:
        log.warn(f"{name} already has that configuration")
        for change in result.unchanged:
            log.detail(changes.unchanged(change))

    if result.applied:
        log.ok(f"updated {name}")
        for change in result.applied:
            log.detail(changes.applied(change))

    if result.needs_sync:
        log.hint(f"run 'mcnet sync {name}' to apply the changes")


@app.command()
@handle
def forget(
    name: Annotated[str, typer.Argument(help="Name of the server to delete")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip the confirmation")
    ] = False,
):
    folder = servers.locate(name)

    if not yes:
        log.warn(f"this will remove the mcnet.yaml of '{name}'")
        log.detail(
            f"loader, version, port and "
            f"{servers.declared_plugins(folder)} declared plugins"
        )

        _confirm(name, "nothing was removed")

    servers.forget(folder)

    log.ok(f"mcnet no longer manages '{name}'")
    log.hint(f"the files in {paths.display(folder)} are untouched")


@app.command()
@handle
def delete(
    name: Annotated[str, typer.Argument(help="Name of the server to delete")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip the confirmation")
    ] = False,
):
    folder = servers.locate(name)

    if not yes:
        log.warn(f"this will delete {paths.display(folder)} and everything in it")

        if servers.has_world(folder):
            log.detail("including the world, which cannot be recovered")

        _confirm(name, "nothing was deleted")

    servers.delete(folder)

    log.ok(f"deleted {paths.display(folder)}")


@app.command()
def show():
    pass
