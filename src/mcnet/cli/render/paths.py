from pathlib import Path


def display(path: Path) -> str:
    """Path relative to the current folder when possible, absolute otherwise."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
