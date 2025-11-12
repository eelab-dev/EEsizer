"""Mock LLM provider for headless testing and CI.

Provides deterministic, configurable responses for the optimizer loop stages:
- analysis_summary
- optimization_suggestion
- sizing (netlist production)

The MockLLM implements a minimal interface: `ask(prompt_type, payload)` and
`call(prompt_type, payload)` to mirror synchronous LLM calls used by `eesizer.llm.base`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import json


class MockLLM:
    """Simple Mock LLM that returns canned responses or rule-based changes.

    Usage:
      mock = MockLLM(config={...})
      resp = mock.call("analysis", {"metrics": {...}})
"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def call(self, prompt_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Return a dict simulating an LLM structured response for given stage."""
        if prompt_type == "analysis":
            return self._analysis_response(payload)
        if prompt_type == "optimize":
            return self._optimize_response(payload)
        if prompt_type == "sizing":
            return self._sizing_response(payload)
        # default: echo
        return {"text": json.dumps(payload)}

    def ask(self, prompt_type: str, payload: Dict[str, Any]) -> str:
        """Return a textual response (compatibility helper)."""
        return json.dumps(self.call(prompt_type, payload))

    def _analysis_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        metrics = payload.get("metrics", {})
        # Simple heuristic: report which metrics are below target if targets provided
        targets = payload.get("targets", {})
        reasons = []
        suggestions = []
        for k, val in metrics.items():
            tgt = targets.get(k)
            if tgt is None:
                continue
            try:
                v = float(val)
                if v < float(tgt):
                    reasons.append(f"{k} below target: {v} < {tgt}")
                    # suggest increasing device size as a generic action
                    suggestions.append({
                        "component": "transistor_m1",
                        "param": "width",
                        "action": "increase",
                        "magnitude": "10%",
                        "rationale": f"{k} below target"
                    })
            except Exception:
                continue
        return {"pass": len(reasons) == 0, "reasons": reasons, "suggestions": suggestions}

    def _optimize_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # For simplicity, just translate suggestions into changes
        suggestions = payload.get("analysis", {}).get("suggestions", [])
        changes = []
        for s in suggestions:
            changes.append({
                "component": s.get("component", "transistor_m1"),
                "param": s.get("param", "width"),
                "action": s.get("action", "increase"),
                "value": s.get("magnitude", "10%"),
                "rationale": s.get("rationale", "auto-suggestion")
            })
        return {"changes": changes}

    def _sizing_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Produce a trivial netlist modification: append a comment line showing applied changes.
        base = payload.get("base_netlist", "")
        changes = payload.get("changes", [])
        if not base:
            return {"error": "no base netlist provided"}
        # Build a minimal 'patched' netlist by appending a comment block with changes
        lines = ["* patched netlist by MockLLM"]
        for c in changes:
            lines.append(f"* change: {c.get('component')} {c.get('param')} {c.get('action')} {c.get('value')}")
        patched = base + "\n" + "\n".join(lines)
        return {"netlist_text": patched}


__all__ = ["MockLLM"]
