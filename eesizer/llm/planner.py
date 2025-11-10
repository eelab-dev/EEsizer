import json
import re
from typing import Any, Dict, List, Tuple

from .schemas import AnalysisType, SimulationType, ToolCall, ToolChain


_JSON_RE = re.compile(r"(\{[\s\S]*\}|\[[\s\S]*\])")


def _find_json_blob(text: str) -> str | None:
    m = _JSON_RE.search(text)
    return m.group(1) if m else None


def extract_tool_data(tool_text: str) -> ToolChain:
    """Extract a tool-chain JSON from an LLM response and validate it.

    The function is resilient: it searches for the first JSON-like blob and attempts to parse it
    into a ToolChain. If parsing fails, it will try some simple heuristics.
    """
    blob = _find_json_blob(tool_text)
    if not blob:
        # last resort: try to parse as python-like dict via eval in safe mode
        raise ValueError("No JSON tool-chain found in LLM response")

    data = json.loads(blob)
    # normalize forms: allow either {'tool_calls': [...]} or just a list
    if isinstance(data, list):
        data = {"tool_calls": data}

    # Validate and construct ToolChain
    tc = ToolChain(**data)
    return tc


def format_simulation_types(tool_data_list: List[Dict[str, Any]]) -> List[str]:
    return [t.get("simulation_type") for t in tool_data_list if t.get("simulation_type")]


def format_simulation_tools(tool_data_list: List[Dict[str, Any]]) -> List[str]:
    return [t.get("simulation_tool") for t in tool_data_list if t.get("simulation_tool")]


def format_analysis_types(tool_data_list: List[Dict[str, Any]]) -> List[str]:
    return [t.get("analysis_type") for t in tool_data_list if t.get("analysis_type")]


def combine_results(sim_types: List[str], sim_tools: List[str], analysis_types: List[str]) -> Dict[str, Any]:
    return {
        "simulation_types": sim_types,
        "simulation_tools": sim_tools,
        "analysis_types": analysis_types,
    }


def get_tasks(tasks_text: str) -> dict:
    """Light helper to parse the notebook's task-generation JSON output.

    The original notebook expected a pure JSON string (sometimes wrapped in backticks or containing
    the word 'json'). We attempt to extract the JSON blob robustly and return the parsed dict.
    """
    blob = _find_json_blob(tasks_text)
    if not blob:
        raise ValueError("No JSON found in tasks_text")
    return json.loads(blob)


def nodes_extract(node_text: str) -> List[str]:
    """Extract node names from a short LLM response (heuristic).

    Returns a list of tokens that look like node names.
    """
    # split on common separators and filter
    parts = re.split(r"[\s,;:\n]+", node_text)
    nodes = [p for p in parts if p and re.match(r"^[A-Za-z0-9_]+$", p)]
    return nodes
