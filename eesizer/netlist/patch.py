"""Netlist patch utilities: safe apply/revert and simple syntax checks.

This module provides small, well-tested helpers used by the Optimizer to apply
netlist edits safely. It favors simplicity and safety: take a full replaced
netlist (the sizing stage should provide a full netlist) and write it atomically
with a timestamped backup of the previous netlist. Also provides a simple
syntactic validator to catch obvious malformed outputs from LLMs.
"""
from __future__ import annotations

import os
import shutil
import datetime
from typing import Tuple


def _timestamp() -> str:
    # use timezone-aware UTC timestamp to avoid deprecation of utcnow()
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def make_backup(path: str) -> str:
    """Create a timestamped backup copy of path and return backup path.

    If the file does not exist, raise FileNotFoundError.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    dirn = os.path.dirname(path) or "."
    base = os.path.basename(path)
    bak = os.path.join(dirn, f"{base}.bak.{_timestamp()}")
    shutil.copy2(path, bak)
    return bak


def apply_netlist_replacement(path: str, new_text: str) -> Tuple[str, int]:
    """Atomically replace the netlist at `path` with `new_text`.

    Returns a tuple (backup_path, bytes_written).
    Creates parent dir if needed.
    """
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    # If existing file present, back it up
    backup = None
    if os.path.exists(path):
        backup = make_backup(path)

    # Write new file to a tmp then atomically move
    tmp_path = f"{path}.tmp.{_timestamp()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    # Replace
    os.replace(tmp_path, path)
    return (backup or "", len(new_text.encode("utf-8")))


def revert_backup(path: str, backup_path: str) -> None:
    """Restore backup_path over path. Raises if backup_path missing."""
    if not os.path.exists(backup_path):
        raise FileNotFoundError(backup_path)
    shutil.copy2(backup_path, path)


def validate_netlist_syntax(netlist_text: str) -> Tuple[bool, str]:
    """Perform a small set of syntactic checks on a netlist string.

    Returns (ok, message). Checks include:
      - matching counts of '.control' and '.endc' (if either present)
      - presence of '.end' or '.endc'
      - reasonable length (> 10 bytes)
    This is intentionally lightweight — it's a fast pre-check to catch obvious
    malformed LLM outputs before writing to disk.
    """
    txt = netlist_text or ""
    if len(txt) < 10:
        return False, "netlist too short"

    lc = txt.lower()
    cnt_control = lc.count(".control")
    cnt_endc = lc.count(".endc")
    if (cnt_control > 0 or cnt_endc > 0) and cnt_control != cnt_endc:
        return False, f"mismatched .control/.endc counts: {cnt_control}/{cnt_endc}"

    if ".end" not in lc and ".endc" not in lc:
        return False, "missing .end or .endc"

    return True, "ok"


__all__ = ["make_backup", "apply_netlist_replacement", "revert_backup", "validate_netlist_syntax"]
