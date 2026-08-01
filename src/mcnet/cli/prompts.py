import typer

from mcnet.errors import McnetError


def confirm_name(name: str, *, refusal: str) -> None:
    """Make the user type the name, or abort saying nothing happened."""
    if typer.prompt(f"Type '{name}' to confirm") != name:
        raise McnetError(f"name does not match, {refusal}")
