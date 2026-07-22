import typer

from mcnet import commands, errors, log

app = typer.Typer()


@app.callback()
def callback():
    """mcnet - declarative manager for Minecraft server networks."""
    pass


@app.command()
def init(
    project_name: str = typer.Option(None, "--name", "-n", help="Name of the project"),
    mc_version: str = typer.Option(
        ..., "--version", "-v", help="Minecraft version to use for plugin compatibility"
    ),
):
    """Create a new mcnet.yaml in the current directory.

    Fails if one already exists. The network name defaults to the
    current folder name.
    """
    try:
        commands.mcnet_init(project_name=project_name, mc_version=mc_version)
    except errors.McnetError as e:
        log.err(str(e))
        raise typer.Exit(code=1)

    log.ok("mcnet initialized successfully")


@app.command()
def add_server(
    server_name: str = typer.Argument(..., help="Name of the server to add"),
    loader: str = typer.Option(
        "paper",
        "--loader",
        "-l",
        help="Loader type for the server (e.g., forge, fabric)",
    ),
    port: int = typer.Option(None, "--port", "-p", help=""),
):
    """Add a server to the network.

    The port is auto-assigned if not given: 25565 for velocity,
    otherwise the next free one.
    """
    try:
        result = commands.mcnet_add_server(
            server_name=server_name, loader=loader, port=port
        )
    except errors.McnetError as e:
        log.err(str(e))
        raise typer.Exit(code=1)

    log.ok(f"added server '{result.server_name}' on port {result.port}")


@app.command()
def edit_server(
    server_name: str = typer.Argument(..., help="Name of the server to add"),
    new_name: str = typer.Option(
        None, "--rename", "-r", help="New name for the server"
    ),
    loader: str = typer.Option(
        None, "--loader", "-l", help="Loader type for the server (e.g., forge, fabric)"
    ),
    port: int = typer.Option(None, "--port", "-p", help=""),
):
    """Change the settings of an existing server."""
    try:
        changes = commands.mcnet_edit_server(
            server_name=server_name, new_name=new_name, loader=loader, port=port
        )
    except errors.McnetError as e:
        log.err(str(e))
        raise typer.Exit(code=1)

    if not changes:
        log.warn("nothing to change")
        return

    log.info("updated server:")

    for change in changes:
        typer.echo(f"\t{change}")


@app.command()
def list():
    """List the servers defined in the network."""
    try:
        servers = commands.mcnet_list()
    except errors.McnetError as e:
        log.err(str(e))
        raise typer.Exit(code=1)

    if not servers:
        log.warn("no servers defined (use 'mcnet add-server')")
        return

    for name, cfg in servers.items():
        typer.echo(f"\t{name:<10} → {cfg.loader:<10} → {cfg.port}")


@app.command()
def add_plugin(
    url: str = typer.Argument(..., help=""),
    server_names: str = typer.Option(
        ...,
        "--server",
        "-s",
        help="Comma-separated list of servers to add the plugin to",
    ),
):
    """Add a plugin to a server from its Modrinth or Hangar URL."""

    try:
        result = commands.mcnet_add_plugin(url=url, server_names=server_names)
    except errors.McnetError as e:
        log.err(str(e))
        raise typer.Exit(code=1)

    for name, reason in result.skipped.items():
        log.warn(f"skipped '{name}': {reason}")

    if not result.compatible:
        log.warn(f"{result.slug}: not added to any server")
        return

    log.ok(f"added {result.slug} to: {', '.join(result.compatible)}")


@app.command()
def sync():
    """Download every plugin declared in the manifest."""
    try:
        result = commands.mcnet_sync()
    except errors.McnetError as e:
        log.err(str(e))
        raise typer.Exit(code=1)

    for key, reason in result.skipped.items():
        log.warn(f"skipped {key}: {reason}")

    if not result.downloaded and not result.skipped:
        log.info("nothing to sync (no plugins in manifest)")
    elif not result.downloaded:
        log.warn("no plugins downloaded — check the skipped list above")
    else:
        log.ok(f"downloaded {len(result.downloaded)} plugin(s)")


@app.command()
def update_plugin():
    """Check for newer plugin versions and update the lockfile."""
