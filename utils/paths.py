from pathlib import Path


def resolve_path(base : str | Path, path : str | Path):
    path = Path(path)

    if path.is_absolute():
        return path.resolve()
    
    return Path(base).resolve() / path

def display_path_rel_to_cwd(base : str | Path, path : str | Path):
    try:
        path = Path(path)
    except Exception:
        return path

    if base:
        try:
            return str(path.relative_to(base))
        except Exception:
            pass
    return str(path)

def is_binary_file(path : str | Path) -> bool:
    try:
        with open(path,"rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except Exception:
        return False