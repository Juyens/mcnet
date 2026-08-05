from pathlib import Path

EULA_NAME = "eula.txt"

ACCEPTED = "eula=true"

NOTICE = (
    "# Accepted through mcnet. The Minecraft EULA is at https://aka.ms/MinecraftEULA"
)


def accepted(folder: Path) -> bool:
    """Whether this server already has the EULA agreed to."""
    path = folder / EULA_NAME

    if not path.exists():
        return False

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip().replace(" ", "").lower()

        if stripped.startswith("eula="):
            return stripped.removeprefix("eula=") == "true"

    return False


def accept(folder: Path) -> Path:
    """Record the agreement. Only ever called once the user has said yes."""
    path = folder / EULA_NAME
    path.write_text(f"{NOTICE}\n{ACCEPTED}\n", encoding="utf-8")

    return path
