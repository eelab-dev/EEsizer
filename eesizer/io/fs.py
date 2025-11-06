import os
from typing import Any


def safe_write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def safe_read(path: str, default: Any = None) -> Any:
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception:
        return default
