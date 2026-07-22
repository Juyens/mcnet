# MCNET

**Declarative plugin management for Minecraft networks**

mcnet is a command-line tool for managing the plugins of a Minecraft network declaratively. The idea behind it is that when you push your network to a repository, you don't have to commit the plugin jars, only the folders with their configurations. It's built with a network in mind, but works just as well for a single server.

## Support

mcnet only supports Modrinth and Hangar as sources, since those are the platforms with open, automation-friendly APIs.

[![Modrinth](https://img.shields.io/badge/Modrinth-00AF5C?style=flat)](https://modrinth.com)
[![Hangar](https://img.shields.io/badge/Hangar-0068D6?style=flat)](https://hangar.papermc.io)

## Installation

Download the binary for your system from the [releases](https://github.com/Juyens/mcnet/releases) page, or install from source:

```bash
git clone https://github.com/Juyens/mcnet.git
cd mcnet
uv tool install .
```

## Usage

Create a manifest and add servers and plugins to your network. `add-plugin` writes the plugin to
the manifest and downloads it right away:

```bash
mcnet init --version 26.1.2
mcnet add-server survival --loader paper
mcnet add-plugin https://modrinth.com/plugin/Chunky --server survival
mcnet add-plugin https://hangar.papermc.io/Gecolay/GSit --server survival
```

When someone clones your repository, the manifest is there but the jars are not. A single command downloads everything the manifest declares:

```bash
mcnet sync
```

## Commands

| Command                               | Description                                 |
| ------------------------------------- | ------------------------------------------- |
| `init`                                | Create a new manifest in the current folder |
| `add-server <name>`                   | Add a server                                |
| `edit-server <name>`                  | Change a server's settings                  |
| `remove-server <name>`                | Remove a server                             |
| `list`                                | List all servers                            |
| `add-plugin <url> --server <a,b>`     | Add a plugin from its Modrinth/Hangar URL   |
| `remove-plugin <slug> --server <a,b>` | Remove a plugin                             |
| `sync`                                | Download all plugins from the manifest      |
| `update [slug]`                       | Update plugins to their latest version      |