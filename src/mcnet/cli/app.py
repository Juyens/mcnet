import typer

from mcnet.cli import context
from mcnet.cli.commands import plugin, proxy, server, sync

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main(ctx: typer.Context) -> None:
    """Declarative manager for Minecraft server networks."""
    context.attach(ctx)


app.add_typer(plugin.app, name="plugin")
app.add_typer(server.app, name="server")
app.add_typer(proxy.app, name="proxy")
app.command(name="sync")(sync.run)
