# MCNET

**Declarative plugin management for Minecraft networks**

mcnet is a command-line tool for managing the plugins of a Minecraft network declaratively. The idea behind it is that when you push your network to a repository, you don't have to commit the plugin jars, only the folders with their configurations. It's built with a network in mind, but works just as well for a single server.

## Support

mcnet only supports Modrinth and Hangar as sources, since those are the platforms with open, automation-friendly APIs.

[![Modrinth](https://img.shields.io/badge/Modrinth-00AF5C?style=flat)](https://modrinth.com)
[![Hangar](https://img.shields.io/badge/Hangar-0068D6?style=flat)](https://hangar.papermc.io)

Server and proxy jars come from the projects that publish them: Paper, Purpur, Folia and Velocity.

## Installation

Download the binary for your system from the [releases](https://github.com/Juyens/mcnet/releases) page, or install from source:

```bash
git clone https://github.com/Juyens/mcnet.git
cd mcnet
uv tool install .
```

Building a server also needs a Java runtime, since mcnet starts it once to generate its files. Minecraft 1.20.5 and newer want Java 21.

## Usage

Each server is a folder with its own manifest. Create them wherever the network should live:

```bash
mcnet server create lobby 1.21.4 paper
mcnet server create survival 1.21.4 paper --port 25566
mcnet proxy create hub 1.21.4 velocity --port 25577
```

Add plugins by their URL, to as many servers as you like at once. The right build is picked for each one, so the same plugin lands as its Paper jar on a server and its Velocity jar on a proxy:

```bash
mcnet plugin add https://modrinth.com/plugin/luckperms lobby survival hub
mcnet plugin add https://hangar.papermc.io/kennytv/Maintenance lobby hub
```

Then build. It downloads the server jars and the plugins, writes the settings the manifests declare, starts each server once so it generates the rest, and leaves a launcher behind:

```bash
mcnet build
```

That leaves a network you can start, and a folder worth committing:

```bash
git add . && git commit -m "my network"
```

The jars stay out of git. What goes in is the manifests, the lockfile pinning exactly which version of everything was resolved, the configs, and the launchers. When someone clones the repository, one command puts it back exactly as it was:

```bash
git clone https://github.com/you/your-network.git
cd your-network
mcnet build
```

If you only want the jars and not a first start, `mcnet sync` does that half on its own. Both take server names, or work on everything in the folder, or on whichever server you happen to be standing in.
