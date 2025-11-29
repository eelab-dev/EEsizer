from dataclasses import dataclass
from typing import List, Any

@dataclass
class OptimizationPlan:
    edits: List[Any]
    rationale: str = ""


class Optimizer:
    def propose(self, netlist_text: str, metrics, spec) -> OptimizationPlan:
        raise NotImplementedError()
