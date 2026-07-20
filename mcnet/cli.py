import typer, yaml

from mcnet import Log, Core, HangarAPI, ModrinthAPI
from pathlib import Path

app = typer.Typer()

hangarApi = HangarAPI()
modrinthApi = ModrinthAPI()

@app.callback()
def callback():
    pass

@app.command()
def init(
    project_name: str = typer.Option(
        None,
        "--name", "-n",
        help="Name of the project"
        ),
    mc_version: str = typer.Option(
        ...,
        "--version", "-v",
        help="Minecraft version to use for plugin compatibility"
        )
    ):
    
    path = Path("mcnet.yaml")

    if path.exists():
        Log.err("mcnet.yaml already exists.")
        raise typer.Exit(code=1)

    Log.ok("Initializing mcnet...")

    if project_name is None:
        project_name = Path.cwd().name
    
    data = {
        "project_name": project_name,
        "mc_version": mc_version,
        "servers": {},
    }
    
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8"
    )
    
    Log.ok("mcnet initialized successfully")
    
@app.command()
def add_server(
    server_name: str = typer.Argument(
        ...,
        help="Name of the server to add"
        ),
    loader: str = typer.Option(
        "paper",
        "--loader", "-l",
        help="Loader type for the server (e.g., forge, fabric)"
        ),
    port: int = typer.Option(
        None,
        "--port", "-p",
        help=""
        ) 
    ):
    
    data = Core.load_manifest()
    
    if server_name in data["servers"]:
        Log.err(f"server '{server_name}' already exists.")
        raise typer.Exit(code=1)
    
    Log.info("Adding server...")
    
    if port is None:
        used_ports = []
        
        for server in data["servers"].values():
            used_ports.append(server["port"])
        
        if loader == "velocity":
            port = 25565 
        else:
            port = max(used_ports or [25565]) + 1
    
    data["servers"][server_name] = {
        "loader": loader,
        "port": port,
        "plugins": [],
    }
    
    Core.save_manifest(data)
    
    Log.ok(f"added server '{server_name}' on port {port}")
    
@app.command()
def edit_server(
    server_name: str = typer.Argument(
        ...,
        help="Name of the server to add"
        ),
    new_name: str = typer.Option(
        None,
        "--rename", "-r",
        help="New name for the server"
        ),
    loader: str = typer.Option(
        None,
        "--loader", "-l",
        help="Loader type for the server (e.g., forge, fabric)"
        ),
    port: int = typer.Option(
        None,
        "--port", "-p",
        help=""
        )
    ):
    
    data = Core.load_manifest()
    
    if server_name not in data["servers"]:
        Log.err(f"server '{server_name}' not found")
        raise typer.Exit(code=1)
    
    server = data["servers"][server_name]
    changes = []
    
    if new_name is not None:
        if new_name is data["servers"]:
            Log.err(f"server '{new_name}' already exists")
            raise typer.Exit(code=1)
        
        data["servers"][new_name] = data["servers"].pop(server_name)
        changes.append(f"server_name: {server_name} → {new_name}")
    
    if loader is not None:
        server["loader"] = loader
        changes.append(f"loader: {server['loader']} → {loader}")
        
    if port is not None:
        server["port"] = port
        changes.append(f"port: {server['port']} → {port}")
        
    if not changes:
        Log.warn("nothing to change")
        raise typer.Exit()
    
    Core.save_manifest(data)
    
    Log.ok(f"updated server.")
    for change in changes:
        typer.echo(f"\t{change}")
        
@app.command()
def list():
    data = Core.load_manifest()
    
    servers = data["servers"]
    
    if not servers:
        Log.warn("no servers defined (use 'mcnet add-server')")
        raise typer.Exit()
    
    typer.echo("Listing the servers...")
    for name, cfg in servers.items():
        typer.echo(f"\t{name:<10} → {cfg['loader']:<10} → {cfg['port']}")

@app.command()
def add_plugin():
    Log.ok("Adding plugin...")

@app.command()
def sync():
    Log.ok("Syncing plugins...")

@app.command()
def update_plugin():
    Log.ok("Updating plugin...")