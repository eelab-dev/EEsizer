import os
import re
from typing import Any

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


def _get_model():
    return os.environ.get("EESIZER_MODEL", "gpt-4o")


def make_chat_completion_request(prompt: str) -> str:
    """Lightweight wrapper around the OpenAI client to return assistant text.

    If OpenAI SDK isn't available this raises a helpful error.
    """
    if OpenAI is None:
        raise RuntimeError(
            "OpenAI SDK not available. Install the openai package or run in an environment with OpenAI client."
        )

    client = OpenAI()
    try:
        resp = client.chat.completions.create(
            model=_get_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            stream=False,
            max_completion_tokens=4000,
        )
    except Exception as e:
        raise

    # Attempt to extract text safely
    try:
        # Some SDKs return .choices; others return more nested shapes
        if hasattr(resp, "choices"):
            content = "".join(
                [c.delta.content if hasattr(c, "delta") and getattr(c.delta, "content", None) is not None else (getattr(c, "message", {}).get("content") if isinstance(getattr(c, "message", {}), dict) else None) or getattr(c, "text", "") for c in resp.choices]
            )
        else:
            content = str(resp)
    except Exception:
        content = str(resp)

    return content


def make_chat_completion_request_function(prompt: str) -> Any:
    """Call the chat completion endpoint with function/tool schema support and return raw response.

    The notebook expects a callable with function-calling capability. We return the raw SDK response
    so the notebook can inspect tool calls.
    """
    if OpenAI is None:
        raise RuntimeError(
            "OpenAI SDK not available. Install the openai package or run in an environment with OpenAI client."
        )

    client = OpenAI()
    resp = client.chat.completions.create(
        model=_get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        stream=False,
    )
    return resp
from typing import Any, Dict


class LLMClient:
    """Abstract wrapper for LLM providers."""

    def chat(self, messages: Any, **kwargs) -> Dict:
        raise NotImplementedError()

    def function_call(self, name: str, arguments: Dict) -> Dict:
        raise NotImplementedError()
