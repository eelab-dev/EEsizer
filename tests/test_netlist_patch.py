import os
import json
from pathlib import Path

from eesizer.netlist.patch import apply_netlist_replacement, make_backup, revert_backup, validate_netlist_syntax


def test_apply_and_revert(tmp_path: Path):
    base_text = ".title TEST\nV1 vdd 0 DC 1.8\n.end\n"
    new_text = ".title TEST_MOD\nV1 vdd 0 DC 1.8\n* changed\n.end\n"

    p = tmp_path / "netlists" / "test.cir"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(base_text)

    # Apply replacement
    backup, nbytes = apply_netlist_replacement(str(p), new_text)
    assert nbytes > 0
    assert p.read_text() == new_text
    assert backup != ""
    assert os.path.exists(backup)

    # Revert
    revert_backup(str(p), backup)
    assert p.read_text() == base_text


def test_validate_netlist_syntax_checks():
    ok, msg = validate_netlist_syntax(".title x\n.end\n")
    assert ok

    ok2, msg2 = validate_netlist_syntax("bad")
    assert not ok2

    # mismatched control/endc
    txt = ".control\nrun\n.end\n"
    ok3, msg3 = validate_netlist_syntax(txt)
    assert not ok3
