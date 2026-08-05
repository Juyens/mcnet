from dataclasses import dataclass

from mcnet.domain import loaders
from mcnet.errors import McnetError

# Verbatim from docs.papermc.io/paper/aikars-flags. Tuned for heaps of 6-10GB,
# which is why they are offered rather than assumed.
AIKAR = (
    "-XX:+UseG1GC",
    "-XX:+ParallelRefProcEnabled",
    "-XX:MaxGCPauseMillis=200",
    "-XX:+UnlockExperimentalVMOptions",
    "-XX:+DisableExplicitGC",
    "-XX:+AlwaysPreTouch",
    "-XX:G1NewSizePercent=30",
    "-XX:G1MaxNewSizePercent=40",
    "-XX:G1HeapRegionSize=8M",
    "-XX:G1ReservePercent=20",
    "-XX:G1HeapWastePercent=5",
    "-XX:G1MixedGCCountTarget=4",
    "-XX:InitiatingHeapOccupancyPercent=15",
    "-XX:G1MixedGCLiveThresholdPercent=90",
    "-XX:G1RSetUpdatingPauseTimePercent=5",
    "-XX:SurvivorRatio=32",
    "-XX:+PerfDisableSharedMem",
    "-XX:MaxTenuringThreshold=1",
)

# Verbatim from docs.papermc.io/velocity/tuning.
VELOCITY = (
    "-XX:+UseG1GC",
    "-XX:G1HeapRegionSize=4M",
    "-XX:+UnlockExperimentalVMOptions",
    "-XX:+ParallelRefProcEnabled",
    "-XX:+AlwaysPreTouch",
    "-XX:MaxInlineLevel=15",
)

NONE: tuple[str, ...] = ()

PRESETS = {"aikar": AIKAR, "velocity": VELOCITY, "none": NONE}

# PaperMC says modern JVMs do well on defaults, so nothing is added unasked.
# A proxy holds no world: its own docs put it at 512MB per 500 players plus a
# gigabyte of room.
SERVER_MEMORY = "4G"
PROXY_MEMORY = "1G"


@dataclass(frozen=True)
class JavaSettings:
    """What a manifest says about the JVM. Absent fields fall back per loader."""

    memory: str | None = None
    flags: str | list[str] | None = None


@dataclass(frozen=True)
class Runtime:
    """The arguments to launch one server with, defaults already filled in."""

    memory: str
    flags: tuple[str, ...]

    def command(self, jar: str, *, nogui: bool) -> list[str]:
        args = [
            "java",
            f"-Xms{self.memory}",
            f"-Xmx{self.memory}",
            *self.flags,
            "-jar",
            jar,
        ]

        if nogui:
            args.append("--nogui")

        return args


def runtime(settings: JavaSettings | None, loader: str) -> Runtime:
    return Runtime(
        memory=_memory(settings, loader),
        flags=_flags(settings.flags if settings else None),
    )


def default_memory(loader: str) -> str:
    return PROXY_MEMORY if loaders.is_proxy(loader) else SERVER_MEMORY


PROXY_JAVA = 17

# Minecraft moved its floor twice: 1.17 to Java 16, 1.18 to 17, 1.20.5 to 21.
_FLOORS = ((1, 20, 5, 21), (1, 18, 0, 17), (1, 17, 0, 16))

OLDEST_JAVA = 8


def required(loader: str, mc_version: str) -> int:
    """The oldest Java that will run this. Wrong answers here read as a crash."""
    if loaders.is_proxy(loader):
        return PROXY_JAVA

    parts = _parts(mc_version)

    for major, minor, patch, java in _FLOORS:
        if parts >= (major, minor, patch):
            return java

    return OLDEST_JAVA


def _parts(mc_version: str) -> tuple[int, ...]:
    numbers = []

    for chunk in mc_version.split("."):
        if not chunk.isdigit():
            break

        numbers.append(int(chunk))

    while len(numbers) < 3:
        numbers.append(0)

    return tuple(numbers)


def takes_nogui(loader: str) -> bool:
    """Proxies have no console to turn off."""
    return not loaders.is_proxy(loader)


def _memory(settings: JavaSettings | None, loader: str) -> str:
    if settings is not None and settings.memory is not None:
        return settings.memory

    return default_memory(loader)


def _flags(chosen: str | list[str] | None) -> tuple[str, ...]:
    if chosen is None:
        return NONE

    if isinstance(chosen, str):
        preset = PRESETS.get(chosen)

        if preset is None:
            raise McnetError(
                f"unknown flag preset: {chosen}",
                hint=f"use one of {', '.join(PRESETS)}, or list the flags yourself",
            )

        return preset

    return tuple(chosen)
