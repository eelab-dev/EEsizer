import os
from typing import Optional

BASE_DIR = os.path.abspath(os.getcwd())


def make_run_dir(run_name: str = "run") -> str:
    out = os.path.join(BASE_DIR, run_name)
    os.makedirs(out, exist_ok=True)
    return out


OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def out_path(name: str, run_dir: Optional[str] = None) -> str:
    """Return an absolute path under OUTPUT_DIR (or run_dir if provided)."""
    base = run_dir or OUTPUT_DIR
    if os.path.isabs(name):
        return name
    return os.path.join(base, os.path.basename(name))
