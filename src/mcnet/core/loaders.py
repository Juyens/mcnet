from enum import StrEnum


class ServerLoader(StrEnum):
    BUKKIT = "bukkit"
    SPIGOT = "spigot"
    PAPER = "paper"
    PURPUR = "purpur"
    FOLIA = "folia"


class ProxyLoader(StrEnum):
    VELOCITY = "velocity"
    WATERFALL = "waterfall"
    BUNGEECORD = "bungeecord"
