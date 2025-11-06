from typing import Any, Dict


class LLMClient:
    """Abstract wrapper for LLM providers."""

    def chat(self, messages: Any, **kwargs) -> Dict:
        raise NotImplementedError()

    def function_call(self, name: str, arguments: Dict) -> Dict:
        raise NotImplementedError()
