import yaml
import typer

from pathlib import Path
from mcnet import Log

class Core:
    @staticmethod
    def load_manifest(path: Path = Path("mcnet.yaml")) -> dict:
        if not path.exists():
            Log.err("mcnet.yaml not found (did you run 'mcnet init'?)")
            raise typer.Exit(code=1)
        
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data["servers"] = data.get("servers") or {}
        return data
    
    @staticmethod
    def save_manifest(data: dict, path = Path("mcnet.yaml")):
        path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )