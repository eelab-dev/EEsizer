from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SimulationType(str, Enum):
    dc = "dc"
    ac = "ac"
    transient = "transient"


class AnalysisType(str, Enum):
    ac_gain = "ac_gain"
    output_swing = "output_swing"
    offset = "offset"
    ICMR = "ICMR"
    tran_gain = "tran_gain"
    bandwidth = "bandwidth"
    unity_bandwidth = "unity_bandwidth"
    phase_margin = "phase_margin"
    power = "power"
    thd_input_range = "thd_input_range"
    cmrr_tran = "cmrr_tran"


class ToolCall(BaseModel):
    name: str
    simulation_type: Optional[SimulationType] = None
    analysis_type: Optional[AnalysisType] = None
    simulation_tool: Optional[str] = None
    args: Optional[Dict[str, Any]] = None


class ToolChain(BaseModel):
    tool_calls: List[ToolCall]


# LLM response schemas for analysis/optimization/sizing


class Suggestion(BaseModel):
    component: str
    param: str
    action: str
    magnitude: Optional[str] = None
    rationale: Optional[str] = None


class AnalysisResponse(BaseModel):
    pass_: bool
    reasons: Optional[List[str]] = []
    suggestions: Optional[List[Suggestion]] = []


class Change(BaseModel):
    component: str
    param: str
    action: str
    value: Optional[str] = None
    rationale: Optional[str] = None


class OptimizeResponse(BaseModel):
    changes: List[Change]


class SizingResponse(BaseModel):
    netlist_text: str
    notes: Optional[str] = None
