from pathlib import Path


def ensure_gitignore(root: Path):
    path = root / ".gitignore"
    rule = "*/plugins/*.jar"

    if path.exists():
        content = path.read_text(encoding="utf-8")
        if rule in content:
            return  # ya está, no dupliques
        content = content.rstrip() + f"\n\n# mcnet: downloaded jars\n{rule}\n"
        path.write_text(content, encoding="utf-8")
    else:
        path.write_text(f"# mcnet: downloaded jars\n{rule}\n", encoding="utf-8")
