from typing import Annotated

import typer

from mcnet.cli import context
from mcnet.cli.handler import handle
from mcnet.cli.render import log
from mcnet.cli.render.plugins import incompatible_line
from mcnet.services import plugin

app = typer.Typer(no_args_is_help=True)


@app.command()
@handle
def add(
    ctx: typer.Context,
    url: Annotated[str, typer.Argument(help="Modrinth or Hangar URL of the plugin")],
    names: Annotated[
        list[str],
        typer.Argument(help="Servers to add it to"),
    ],
    download: Annotated[
        bool,
        typer.Option("--download/--no-download", help="Download the jar right away"),
    ] = True,
):
    """Declare a plugin on one or more servers."""
    current = context.session(ctx)

    result = plugin.add(
        url,
        names,
        current.providers,
        downloader=current.downloader if download else None,
    )

    if result.added:
        log.ok(f"added '{result.slug}' to {', '.join(result.added)}")

    if result.downloaded:
        log.detail(f"downloaded into {', '.join(result.downloaded)}")

    if result.already:
        log.warn(f"'{result.slug}' was already in {', '.join(result.already)}")

    for target in result.incompatible:
        log.warn(f"skipped {target.name}: {incompatible_line(target)}")

    for target in result.failed:
        log.warn(f"could not download for {target.name}: {target.reason}")

    for name in result.unknown:
        log.err(f"no server named '{name}'")

    if not result.verified:
        log.warn("could not check compatibility with Modrinth")

    if result.pending or result.failed or not result.verified:
        log.hint("run 'mcnet sync' to download it")

    if result.unknown:
        raise typer.Exit(code=1)


@app.command()
@handle
def remove(
    slug: Annotated[str, typer.Argument(help="Slug of the plugin")],
    names: Annotated[
        list[str],
        typer.Argument(help="Servers to remove it from"),
    ],
    delete_jar: Annotated[
        bool,
        typer.Option("--delete-jar/--keep-jar", help="Delete the jar as well"),
    ] = True,
):
    """Stop declaring a plugin on one or more servers."""
    result = plugin.remove(slug, names, delete_jar=delete_jar)

    if result.removed:
        log.ok(f"removed '{result.slug}' from {', '.join(result.removed)}")

    if result.deleted:
        log.detail(f"deleted the jar from {', '.join(result.deleted)}")

    if result.missing:
        log.warn(f"'{result.slug}' was not in {', '.join(result.missing)}")

    for target in result.failed:
        log.warn(target.reason)

    for name in result.unknown:
        log.err(f"no server named '{name}'")

    if result.removed and not delete_jar:
        log.hint("the jar is still in plugins/, mcnet no longer tracks it")

    if result.failed:
        log.hint("stop the server and try again")

    if result.unknown or result.failed:
        raise typer.Exit(code=1)