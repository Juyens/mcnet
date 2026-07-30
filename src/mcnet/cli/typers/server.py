import shutil
from pathlib import Path
from typing import Annotated

import typer

from mcnet.cli import callbacks
from mcnet.cli.changes import Changes
from mcnet.cli.handler import handle
from mcnet.core import log, paths
from mcnet.core.error import McnetError
from mcnet.core.loaders import ServerLoader
from mcnet.core.models import Manifest
from mcnet.manifest import load_manifest, remove_manifest, save_manifest, server_folder

app = typer.Typer(no_args_is_help=True)


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
    target = Path.cwd() / name

    if target.exists():
        raise McnetError(
            f"{paths.display(target)} already exists",
            hint="pick another name, or remove the folder first",
        )

    target.mkdir(parents=True)

    server = Manifest(
        loader=loader.value,
        mc_version=mc_version,
        port=port,
        plugins=[],
    )
    manifest_path = save_manifest(server, target)

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
    folder = server_folder(name)
    manifest = load_manifest(folder)

    changes = Changes()
    needs_sync = False

    if loader is not None:
        if changes.record("loader", manifest.loader, loader.value):
            manifest.loader = loader.value
            needs_sync = True

    if mc_version is not None:
        if changes.record("version", manifest.mc_version, mc_version):
            manifest.mc_version = mc_version
            needs_sync = True

    if port is not None:
        if changes.record("port", manifest.port, port):
            manifest.port = port

    if not changes.applied and not changes.already:
        log.warn("nothing to change")
        raise typer.Exit()

    if changes.already:
        log.warn(f"{name} already has that configuration")
        for line in changes.already:
            log.detail(line)

    if changes.applied:
        save_manifest(manifest, folder)

        log.ok(f"updated {name}")
        for line in changes.applied:
            log.detail(line)

    if needs_sync:
        log.hint(f"run 'mcnet sync {name}' to apply the changes")


@app.command()
@handle
def forget(
    name: Annotated[str, typer.Argument(help="Name of the server to delete")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip the confirmation")
    ] = False,
):
    folder = server_folder(name)

    if not yes:
        manifest = load_manifest(folder)

        log.warn(f"this will remove the mcnet.yaml of '{name}'")
        log.detail(
            f"loader, version, port and {len(manifest.plugins)} declared plugins"
        )

        if typer.prompt(f"Type '{name}' to confirm") != name:
            raise McnetError("name does not match, nothing was removed")

    remove_manifest(folder)

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
    folder = server_folder(name)

    if not yes:
        log.warn(f"this will delete {paths.display(folder)} and everything in it")

        if (folder / "world").exists():
            log.detail("including the world, which cannot be recovered")

        if typer.prompt(f"Type '{name}' to confirm") != name:
            raise McnetError("name does not match, nothing was deleted")

    shutil.rmtree(folder)

    log.ok(f"deleted {paths.display(folder)}")


@app.command()
def show():
    pass
