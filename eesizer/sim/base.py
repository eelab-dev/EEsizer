from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SimulationRequest:
    sim_type: str  # 'dc'|'ac'|'tran'
    options: Dict = None


@dataclass
class SimulationResult:
    success: bool
    output_files: Dict[str, str]
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class Simulator:
    def run(self, netlist_text: str, request: SimulationRequest) -> SimulationResult:
        raise NotImplementedError()
