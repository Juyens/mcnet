from typing import Annotated

import typer

from mcnet.cli import context
from mcnet.cli.handler import handle
from mcnet.cli.render import log, progress
from mcnet.domain.results import ServerSync
from mcnet.services import sync as service


@handle
def run(
    ctx: typer.Context,
    name: Annotated[
        str | None,
        typer.Argument(help="Server to sync, or every one here"),
    ] = None,
    jobs: Annotated[
        int,
        typer.Option("--jobs", "-j", help="Downloads to run at once", min=1, max=32),
    ] = service.DEFAULT_WORKERS,
):
    """Install what the manifests declare: server jars and plugins."""
    current = context.session(ctx)
    targets = service.targets(name)

    with progress.RichSink() as sink:
        result = service.sync(
            targets,
            current.providers,
            current.downloader,
            current.cache,
            workers=jobs,
            sink=sink,
        )

    for server in result.servers:
        _report(server)

    if result.failed:
        raise typer.Exit(code=1)


def _report(server: ServerSync) -> None:
    if server.failed:
        log.warn(f"{server.name}: {_counts(server)}")
    elif server.touched:
        log.ok(f"{server.name}: {_counts(server)}")
    else:
        log.info(f"  {server.name} is up to date")

    for filename in server.downloaded:
        log.detail(f"+ {filename}")

    for filename in server.removed:
        log.detail(f"- {filename}")

    for failure in server.failed:
        log.detail(f"x {failure.name}: {failure.reason}")


def _counts(server: ServerSync) -> str:
    parts = []

    if server.downloaded:
        parts.append(f"{len(server.downloaded)} downloaded")

    if server.removed:
        parts.append(f"{len(server.removed)} removed")

    if server.current:
        parts.append(f"{len(server.current)} up to date")

    if server.failed:
        parts.append(f"{len(server.failed)} failed")

    return ", ".join(parts)
