from collections.abc import Sequence
from typing import ClassVar

from rich.highlighter import RegexHighlighter
from rich.theme import Theme

from mcnet.domain.loaders import ProxyLoader, ServerLoader

_LOADER_COLORS = {
    "paper": "bright_white",
    "purpur": "bright_magenta",
    "folia": "bright_green",
    "velocity": "bright_blue",
}

_LOADER_PATTERNS = []
_LOADER_STYLES = {}

for loader in [*ServerLoader, *ProxyLoader]:
    _LOADER_PATTERNS.append(rf"(?P<{loader}>\b{loader}\b)")
    _LOADER_STYLES[f"mcnet.{loader}"] = _LOADER_COLORS.get(loader, "green")


class McnetHighlighter(RegexHighlighter):
    base_style = "mcnet."
    highlights: ClassVar[Sequence[str]] = [
        r"(?P<quoted>'[^']*')",
        r"(?P<number>\b\d+(\.\d+)+\b|\b\d{4,5}\b)",
        r"(?P<path>\b[\w-]+[\\/][\w./\\-]+)",
        *_LOADER_PATTERNS,
    ]


THEME = Theme(
    {
        "mcnet.quoted": "cyan",
        "mcnet.number": "magenta",
        "mcnet.path": "blue",
        **_LOADER_STYLES,
    }
)
