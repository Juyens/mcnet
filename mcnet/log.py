import typer

class Log:
    PREFIX = "[mcnet]"
    
    @classmethod
    def info(cls, message: str):
        typer.secho(f"{cls.PREFIX} {message}")

    @classmethod
    def ok(cls, message: str):
        typer.secho(f"{cls.PREFIX} {message}", fg=typer.colors.GREEN)

    @classmethod
    def warn(cls, message: str):
        typer.secho(f"{cls.PREFIX} {message}", fg=typer.colors.YELLOW)

    @classmethod
    def err(cls, message: str):
        typer.secho(f"{cls.PREFIX} {message}", fg=typer.colors.RED, err=True)