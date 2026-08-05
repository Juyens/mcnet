import shutil
from pathlib import Path

from mcnet import hashing, paths
from mcnet.domain.models import LockedJar
from mcnet.errors import McnetError

JARS_DIR = "jars"

PART_SUFFIX = ".part"


class JarCache:
    """Jars kept by hash, so the same file is fetched once for a whole network.

    Five paper servers declaring the same plugin want the same bytes, and a
    lock already names them by hash: that makes the hash the obvious key, and
    a second sync anywhere on the machine free.
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = (root or paths.cache_dir()) / JARS_DIR

    def path(self, entry: LockedJar) -> Path:
        return self._root / entry.algorithm / entry.hash

    def holds(self, entry: LockedJar) -> bool:
        return hashing.file_matches(self.path(entry), entry.hash, entry.algorithm)

    def take(self, entry: LockedJar, dest: Path) -> None:
        """Copy a cached jar into place, leaving nothing behind if it fails."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + PART_SUFFIX)

        try:
            shutil.copyfile(self.path(entry), part)
            part.replace(dest)
        except OSError as e:
            part.unlink(missing_ok=True)
            raise McnetError(f"could not write {dest.name}: {e.strerror or e}") from e
        except BaseException:
            part.unlink(missing_ok=True)
            raise
