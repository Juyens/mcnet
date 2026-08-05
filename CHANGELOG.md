# Changelog

Each release takes its notes from the section below that matches its tag, so
what is written here is what appears on the release page.

## 0.2.0 - 2026-08-05

A rewrite. Each server is now a folder that describes itself, pins what it resolved, and can be put back together anywhere.

### What's new

**A lockfile per server.** Every jar is pinned by version, url and hash. A fresh clone reproduces a network byte for byte, without asking any API.

**Server and proxy jars.** Paper, Purpur, Folia and Velocity, fetched and pinned alongside the plugins from Modrinth and Hangar.

**`mcnet build`.** Writes what the manifest declares, starts each server once so it generates its own files, and leaves launchers for Windows and Linux behind. Accepting the Minecraft EULA is asked once, never assumed.

**Faster syncs.** Downloads are keyed by hash and fetched in parallel into a cache shared across the machine, so a network of five servers fetches each distinct jar once instead of five times.

### Quick start

```bash
mcnet server create lobby 1.21.4 paper
mcnet proxy create hub 1.21.4 velocity --port 25577
mcnet plugin add https://modrinth.com/plugin/luckperms lobby hub
mcnet build
```

Commit the folder. When someone clones it, `mcnet build` puts it back exactly as it was.

### Breaking changes

- Manifests written by 0.1.0 do not load. The manifest is now one file per server folder rather than one at the root.
- Every command was renamed: `add-server` is `server create`, `add-plugin` is `plugin add`, and so on. Run `mcnet --help`.
- Spigot, Bukkit, BungeeCord and Waterfall are gone. None of them can be downloaded automatically, and their own authors no longer recommend them.

### Not back yet

`update` and `list` from 0.1.0 have not been rewritten yet.

### Requirements

`mcnet build` starts your server once, so it needs a Java runtime. Minecraft 1.20.5 and newer want Java 21.

## 0.1.0 - 2026-07-22

First release.

Declarative plugin management from a single manifest at the root of a network, with plugins resolved from Modrinth and Hangar and a lockfile pinning what was downloaded.

Commands: `init`, `add-server`, `edit-server`, `remove-server`, `list`, `add-plugin`, `remove-plugin`, `sync`, `update`.
