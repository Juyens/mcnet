import typer

from mcnet.cli.typers import plugin, proxy, server

app = typer.Typer()
app.add_typer(plugin.app, name="plugin")
app.add_typer(server.app, name="server")
app.add_typer(proxy.app, name="proxy")
