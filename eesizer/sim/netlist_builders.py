import re
from typing import List


CONTROL_BLOCK_RE = re.compile(r"^\s*\.control[\s\S]*?\.endc\s*$", re.MULTILINE)


def strip_control_blocks(netlist_text: str) -> str:
    """Remove all .control/.endc blocks from a netlist in an idempotent way."""
    return re.sub(CONTROL_BLOCK_RE, "", netlist_text)


def append_control_block(netlist_text: str, control_block: str) -> str:
    """Append a control block before .end.

    Requires that the netlist contains a line starting with '.end'.
    """
    if ".end" not in netlist_text:
        raise ValueError("Netlist missing .end terminator")
    end_idx = netlist_text.lower().rfind(".end")
    return netlist_text[:end_idx] + control_block + netlist_text[end_idx:]


def _signals_to_str(signals: List[str]) -> str:
    return " ".join(s for s in signals if s)


def build_ac_netlist(
    base_netlist: str,
    signals: List[str],
    outfile: str = "output_ac.dat",
    ac_cmd: str = "ac dec 10 1 1e9",
) -> str:
    """Create an AC simulation netlist writing selected signals to a data file.

    - signals: nodes or expressions supported by wrdata
    - outfile: file name (relative) written by ngspice wrdata
    - ac_cmd: ac command line (e.g., 'ac dec 10 1 1e9')
    """
    clean = strip_control_blocks(base_netlist)
    sigs = _signals_to_str(signals)
    control = f"""
    .control
      {ac_cmd}
      wrdata {outfile} {sigs}
    .endc
    """
    return append_control_block(clean, control)


def build_tran_netlist(
    base_netlist: str,
    signals: List[str],
    outfile: str = "output_tran.dat",
    tran_cmd: str = "tran 50n 500u",
) -> str:
    clean = strip_control_blocks(base_netlist)
    sigs = _signals_to_str(signals)
    control = f"""
    .control
      {tran_cmd}
      wrdata {outfile} {sigs}
    .endc
    """
    return append_control_block(clean, control)


def build_dc_netlist(
    base_netlist: str,
    sweep_cmd: str = "dc Vcm 0 1.2 0.001",
    signals: List[str] = None,
    outfile: str = "output_dc.dat",
) -> str:
    signals = signals or []
    clean = strip_control_blocks(base_netlist)
    sigs = _signals_to_str(signals)
    control = f"""
    .control
      {sweep_cmd}
      wrdata {outfile} {sigs}
    .endc
    """
    return append_control_block(clean, control)
