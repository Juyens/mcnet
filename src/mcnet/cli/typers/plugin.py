import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def add():
    pass


@app.command()
def remove():
    pass


@app.command()
def show():
    pass


@app.command()
def search():
    pass
