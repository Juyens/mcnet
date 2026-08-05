import os
import re
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from mcnet.errors import McnetError

# Both Paper and Velocity announce themselves the same way once they are up.
READY = "Done ("

# Long enough for a world to generate on a slow disk, short enough that a
# wedged server does not hold the terminal forever.
BOOT_TIMEOUT = 900

STOP_TIMEOUT = 120

_VERSION = re.compile(r'version "(\d+)(?:\.(\d+))?')


class Runner(Protocol):
    """Anything that can run a server until it is ready and then stop it.

    Whether a usable Java is around is the runner's problem, not the caller's:
    a fake has no use for one, and asking the machine before delegating would
    make every test depend on what happens to be installed.
    """

    def boot(
        self,
        folder: Path,
        command: list[str],
        *,
        stop: str,
        needs_java: int,
        watch: Callable[[str], None] | None = None,
    ) -> None: ...


class Java:
    """Runs the real thing, watching its output for the line that says it is up."""

    def boot(
        self,
        folder: Path,
        command: list[str],
        *,
        stop: str,
        needs_java: int,
        watch: Callable[[str], None] | None = None,
    ) -> None:
        self._require(needs_java)

        process = subprocess.Popen(
            command,
            cwd=folder,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        guard = threading.Timer(BOOT_TIMEOUT, process.kill)
        guard.start()

        try:
            self._watch(process, stop=stop, watch=watch)
        except BaseException:
            process.kill()
            raise
        finally:
            guard.cancel()

    def _require(self, needs_java: int) -> None:
        """Refuse in words, since the JVM's own complaint is a stack trace."""
        found = installed()

        if found is None:
            raise McnetError(
                f"Java {needs_java} is needed to start a server, and none was found",
                hint="install it, or set JAVA_HOME to point at it",
            )

        if found < needs_java:
            raise McnetError(f"needs Java {needs_java}, found Java {found}")

    def _watch(
        self,
        process: subprocess.Popen[str],
        *,
        stop: str,
        watch: Callable[[str], None] | None,
    ) -> None:
        assert process.stdout is not None
        assert process.stdin is not None

        for line in process.stdout:
            if watch is not None:
                watch(line.rstrip())

            if READY in line:
                process.stdin.write(f"{stop}\n")
                process.stdin.flush()
                break
        else:
            # The pipe closed without the server ever saying it was up.
            raise McnetError(
                "the server stopped before it finished starting",
                hint="check logs/latest.log in the server folder",
            )

        if process.wait(timeout=STOP_TIMEOUT) != 0:
            raise McnetError(f"the server exited with code {process.returncode}")


def installed() -> int | None:
    """Major version of the Java on PATH, or None when there is none."""
    try:
        done = subprocess.run(
            [executable(), "-version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except OSError, subprocess.SubprocessError:
        return None

    # -version writes to stderr, and has since forever.
    return _major(done.stderr or done.stdout)


def executable() -> str:
    home = os.environ.get("JAVA_HOME")

    if home:
        return str(Path(home) / "bin" / "java")

    return "java"


def _major(text: str) -> int | None:
    found = _VERSION.search(text)

    if found is None:
        return None

    first = int(found.group(1))

    # Java 8 and older called themselves 1.8, so the real number is second.
    if first == 1 and found.group(2) is not None:
        return int(found.group(2))

    return first
