"""Lightweight LLM helpers for EEsizer.

This module provides small wrappers for ChatCompletion-style calls (delegating to
an OpenAI-like client when available) and robust parsing utilities to extract
tool call arguments returned via function-calling/tool-calls. The goal is to
centralize parsing and sanitization so notebooks can import these helpers and
avoid duplicated brittle code.

Notes:
- The API call wrappers attempt to instantiate an OpenAI client (from
  `openai import OpenAI`) if no `client` is provided. If the environment or
  package is not available, the wrappers will raise a clear error instructing
  the caller to pass an explicit client.
- Parsing helpers are defensive: they search for JSON-like substrings and try
  to decode concatenated/garbled outputs.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


def _get_default_client():
    try:
        from openai import OpenAI

        return OpenAI()
    except Exception as e:
        raise RuntimeError(
            "No OpenAI client available. Either install/configure `openai` or pass a `client=` argument to the helper function."
        ) from e


def make_chat_completion_request(
    prompt: str,
    client: Optional[Any] = None,
    model: str = "gpt-4o",
    stream: bool = False,
    **kwargs,
) -> str:
    """Call the chat completion API and return the assistant text.

    This is a thin wrapper that expects an OpenAI-like client with
    `client.chat.completions.create(...)`. If no client is supplied the helper
    will try to construct a default client using `openai.OpenAI()`.
    """
    if client is None:
        client = _get_default_client()

    # We call the canonical method used in the notebooks: client.chat.completions.create
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=stream,
            **kwargs,
        )
    except Exception as e:
        raise RuntimeError("LLM request failed: " + str(e)) from e

    # If streaming, notebooks previously iterated over `resp` chunks. For a
    # convenience return the concatenated content when not streaming.
    if stream:
        # Return the response object for callers that want to iterate.
        return resp

    # Non-streaming: try common access patterns
    try:
        # OpenAI-like: resp.choices[0].message.content
        return resp.choices[0].message.content
    except Exception:
        # Fallback: the SDK may return response.choices[0].text
        try:
            return resp.choices[0].text
        except Exception:
            # Last resort: serialize the object
            return json.dumps(resp, default=str)


def make_chat_completion_request_function(
    prompt: str, client: Optional[Any] = None, model: str = "gpt-4o"
) -> Any:
    """Call the chat completion API with function-calling/tools enabled.

    The caller should pass any `tools`/`tool_choice` via kwargs on the client
    call if they want custom tools. This wrapper only provides a straightforward
    call and returns the raw response object for callers that want to inspect
    tool_calls.
    """
    if client is None:
        client = _get_default_client()

    try:
        resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], stream=False)
        return resp
    except Exception as e:
        raise RuntimeError("LLM function-call request failed: " + str(e)) from e


_JSON_CANDIDATE_RE = re.compile(r"(\{.*?\}|\[.*?\])", re.DOTALL)


def _try_load_json_candidates(text: str) -> List[Any]:
    """Find JSON-like blocks in `text` and attempt to json.loads them.

    This helps with model outputs that include surrounding explanation text or
    multiple concatenated JSON objects.
    """
    candidates = []
    for m in _JSON_CANDIDATE_RE.finditer(text):
        s = m.group(0)
        try:
            candidates.append(json.loads(s))
        except Exception:
            # Try to fix simple concatenation issues: if it looks like `}{` or `}{` in a row,
            # try wrapping candidates into an array
            try:
                # sometimes models return multiple JSON objects without a surrounding list
                fixed = "[" + s.replace("}\n{", "},{") + "]"
                parsed = json.loads(fixed)
                candidates.extend(parsed if isinstance(parsed, list) else [parsed])
            except Exception:
                # ignore unparsable candidate
                continue
    return candidates


def extract_tool_data(tool_response: Any) -> List[Dict[str, Any]]:
    """Extract tool-call argument objects from a function-calling response.

    The function accepts either the raw response object returned by the OpenAI
    SDK or a plain dictionary/string. It attempts multiple strategies:
    - Inspect `choices[*].message.tool_calls[*].function.arguments` entries
    - Inspect any JSON-like substrings in the top-level text
    - Return a list of parsed dicts (empty list when nothing found)
    """
    parsed: List[Dict[str, Any]] = []

    # If it's a mapping-like object, drill into common fields
    try:
        # Support both SDK objects and plain dicts
        if hasattr(tool_response, "choices"):
            choices = getattr(tool_response, "choices")
        else:
            choices = tool_response.get("choices", []) if isinstance(tool_response, dict) else []

        for ch in choices:
            # message -> tool_calls -> function -> arguments
            try:
                msg = ch.message if hasattr(ch, "message") else ch.get("message", {})
                tool_calls = msg.get("tool_calls", []) if isinstance(msg, dict) else getattr(msg, "tool_calls", [])
            except Exception:
                tool_calls = []

            for tc in tool_calls:
                # args may be in tc.function.arguments or similar
                arg = None
                try:
                    arg = tc.function.arguments if hasattr(tc, "function") else tc.get("function", {}).get("arguments")
                except Exception:
                    arg = None

                if isinstance(arg, str):
                    parsed.extend(_try_load_json_candidates(arg))
                elif isinstance(arg, dict):
                    parsed.append(arg)

    except Exception:
        # Fallthrough to generic text-based extraction
        pass

    # Generic fallback: try to parse JSON-like substrings from any string representation
    if not parsed:
        text = None
        if isinstance(tool_response, str):
            text = tool_response
        else:
            try:
                text = json.dumps(tool_response)
            except Exception:
                text = str(tool_response)

        if text:
            parsed.extend(x for x in _try_load_json_candidates(text) if isinstance(x, dict))

    # Ensure result is a list of dicts
    return [p for p in parsed if isinstance(p, dict)]


def format_simulation_types(tool_data_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Return a list of simulation-type dicts with defensive handling.

    Example output: [{"name": "ac_simulation"}, {"name": "dc_simulation"}]
    """
    types = set()
    for d in tool_data_list:
        t = d.get("simulation_type") or d.get("sim_type")
        if isinstance(t, str):
            t = t.lower()
            if t in ("ac", "ac_simulation"):
                types.add("ac_simulation")
            elif t in ("dc", "dc_simulation"):
                types.add("dc_simulation")
            elif t in ("transient", "tran", "transient_simulation"):
                types.add("tran_simulation")

    return [{"name": x} for x in sorted(types)]


def format_simulation_tools(tool_data_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Return a list of simulation tool dicts (e.g. run_ngspice).

    Defensive: if no simulation_tool values are present, return an empty list.
    """
    tools = set()
    for d in tool_data_list:
        st = d.get("simulation_tool") or d.get("sim_tool") or d.get("tool")
        if isinstance(st, str):
            tools.add(st.strip())
    return [{"name": t} for t in sorted(tools)]


def format_analysis_types(tool_data_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Return an ordered list of analysis-type dicts.

    This function preserves the order found in the input list and filters to a
    known set of analyses. Unknown analyses are included as-is.
    """
    allowed = {
        "ac_gain",
        "output_swing",
        "offset",
        "icmr",
        "tran_gain",
        "bandwidth",
        "unity_bandwidth",
        "phase_margin",
        "power",
        "thd_input_range",
        "cmrr_tran",
    }
    out: List[Dict[str, str]] = []
    for d in tool_data_list:
        a = d.get("analysis_type") or d.get("analysis") or d.get("analysis_type_name")
        if not a:
            continue
        name = a.strip().lower()
        if name in allowed:
            out.append({"name": name})
        else:
            out.append({"name": name})
    return out


def combine_results(sim_types: List[Dict[str, str]], sim_tools: List[Dict[str, str]], analysis_types: List[Dict[str, str]]) -> Dict[str, Any]:
    """Combine the formatted pieces into a tool_chain like structure.

    Returns a dict: {"tool_calls": [ {"name": ...}, ... ]}
    The combined order is: sim_tools -> sim_types -> analysis_types (tools first
    so the executor knows which tool to run before analyses).
    """
    calls: List[Dict[str, str]] = []
    # prefer explicit tools
    calls.extend(sim_tools)
    # include sim types afterwards (these are conceptual markers)
    calls.extend(sim_types)
    # finally analyses
    calls.extend(analysis_types)
    return {"tool_calls": calls}
