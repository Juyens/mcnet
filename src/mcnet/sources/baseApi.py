from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Resolved:
    filename: str
    url: str
    hash: str
    algorithm: str
    version: str


class BaseApi(ABC):
    USER_AGENT = "juyens/mcnet (joseph.juliuscb@gmail.com)"

    @abstractmethod
    def resolve(self, slug: str, loader: str, mc_version: str) -> "Resolved | None":
        """Return the matching jar, or None if no compatible version exists."""
        ...
