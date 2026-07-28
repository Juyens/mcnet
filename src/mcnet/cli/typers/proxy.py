import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def create():
    pass


@app.command()
def delete():
    pass


@app.command()
def connect():
    pass


@app.command()
def disconnect():
    pass


@app.command()
def show():
    pass
