"""Validation helpers for LLM outputs.

Provides functions to coerce or validate LLM responses against Pydantic schemas
defined in `eesizer.llm.schemas`.
"""
from __future__ import annotations

import json
from typing import Any, Tuple

from .schemas import AnalysisResponse, OptimizeResponse, SizingResponse


def _ensure_dict(obj: Any):
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        # try to extract JSON blob
        try:
            return json.loads(obj)
        except Exception:
            # last resort: try to coerce by finding first {..}
            import re

            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", obj)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
    raise ValueError("Unable to coerce LLM output to JSON/dict")


def validate_analysis(raw: Any) -> AnalysisResponse:
    d = _ensure_dict(raw)
    # map possible 'pass' key to 'pass_'
    if "pass" in d and "pass_" not in d:
        d["pass_"] = d.pop("pass")
    # Use Pydantic v2 API if available
    if hasattr(AnalysisResponse, "model_validate"):
        return AnalysisResponse.model_validate(d)
    return AnalysisResponse.parse_obj(d)


def validate_optimize(raw: Any) -> OptimizeResponse:
    d = _ensure_dict(raw)
    if hasattr(OptimizeResponse, "model_validate"):
        return OptimizeResponse.model_validate(d)
    return OptimizeResponse.parse_obj(d)


def validate_sizing(raw: Any) -> SizingResponse:
    d = _ensure_dict(raw)
    if hasattr(SizingResponse, "model_validate"):
        return SizingResponse.model_validate(d)
    return SizingResponse.parse_obj(d)


__all__ = ["validate_analysis", "validate_optimize", "validate_sizing"]
