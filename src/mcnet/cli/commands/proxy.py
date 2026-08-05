from typing import Annotated

import typer

from mcnet.cli import callbacks
from mcnet.cli.handler import handle
from mcnet.cli.prompts import confirm_name
from mcnet.cli.render import log
from mcnet.cli.render.changes import applied_line, unchanged_line
from mcnet.cli.render.paths import display_path
from mcnet.domain.loaders import ProxyLoader
from mcnet.services import workspace

app = typer.Typer(no_args_is_help=True)


@app.command()
@handle
def create(
    name: Annotated[
        str, typer.Argument(help="Name of the proxy", callback=callbacks.validate_name)
    ],
    mc_version: Annotated[
        str,
        typer.Argument(help="Minecraft version", callback=callbacks.validate_version),
    ],
    loader: Annotated[
        ProxyLoader,
        typer.Argument(help="Proxy software to run"),
    ] = ProxyLoader.VELOCITY,
    port: Annotated[
        int,
        typer.Option(
            "--port", "-p", help="Port the proxy listens on", min=1024, max=65535
        ),
    ] = 25565,
):
    """Create a proxy in the current folder"""
    manifest_path = workspace.create(
        name, loader=loader.value, mc_version=mc_version, port=port
    )

    log.ok(f"created '{name}' ({loader.value}) on port {port}")
    log.hint(f"manifest written to {display_path(manifest_path)}")
    log.hint("run 'mcnet sync' to download the server jar")


@app.command()
@handle
def edit(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the proxy to edit", callback=callbacks.validate_name
        ),
    ],
    loader: Annotated[
        ProxyLoader | None,
        typer.Option("--loader", "-l", help="Proxy software to run"),
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
            "--port", "-p", help="Port the proxy listens on", min=1024, max=65535
        ),
    ] = None,
):
    """Change the settings of a proxy"""
    folder = workspace.locate(name)
    changes = workspace.edit(
        folder,
        loader=None if loader is None else loader.value,
        mc_version=mc_version,
        port=port,
    )

    if not changes.applied and not changes.unchanged:
        log.warn("nothing to change")
        raise typer.Exit()

    if changes.unchanged:
        log.warn(f"{name} already has that configuration")
        for change in changes.unchanged:
            log.detail(unchanged_line(change))

    if changes.applied:
        log.ok(f"updated {name}")
        for change in changes.applied:
            log.detail(applied_line(change))

    if changes.needs_sync:
        log.hint(f"run 'mcnet sync {name}' to apply the changes")


@app.command()
@handle
def forget(
    name: Annotated[str, typer.Argument(help="Name of the proxy to delete")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip the confirmation")
    ] = False,
):
    """Stop managing a proxy, leaving its files alone."""
    folder = workspace.locate(name)

    if not yes:
        log.warn(f"this will remove the mcnet.yaml of '{name}'")
        log.detail(
            f"loader, version, port and "
            f"{workspace.declared_plugins(folder)} declared plugins"
        )

        confirm_name(name, refusal="nothing was removed")

    workspace.forget(folder)

    log.ok(f"mcnet no longer manages '{name}'")
    log.hint(f"the files in {display_path(folder)} are untouched")


@app.command()
@handle
def delete(
    name: Annotated[str, typer.Argument(help="Name of the proxy to delete")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip the confirmation")
    ] = False,
):
    """Delete a proxy and everything in its folder."""
    folder = workspace.locate(name)

    if not yes:
        log.warn(f"this will delete {display_path(folder)} and everything in it")

        confirm_name(name, refusal="nothing was deleted")

    workspace.delete(folder)

    log.ok(f"deleted {display_path(folder)}")
