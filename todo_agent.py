"""
todo_agent.py — The agent under protection.

A minimal coding agent: an LLM with file tools. Deliberately minimal so
feature creep is EASY — drift must be realistic for the demo to be honest.

Backend failover (same pattern as providers.py): tries each (provider,
model) pair until one answers. Reorder AGENT_BACKENDS based on diag_tools.py.
"""
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from sandbox_tools import TOOL_SCHEMAS, run_tool

load_dotenv()

_BACKENDS = {
    "gemini": ("GEMINI_API_KEY",
               "https://generativelanguage.googleapis.com/v1beta/openai/"),
    "nvidia": ("NVIDIA_API_KEY",
               "https://integrate.api.nvidia.com/v1"),
}

# Tried in order.
# gemini-3.5-flash: PROVEN native tool support on this key (diag_tools.py).
# NVIDIA models: chat works (protocol fallback), native tools not emitted.
AGENT_BACKENDS = [
    ("gemini", "gemini-3.5-flash"),      # native tools — primary agent brain
    ("nvidia", "openai/gpt-oss-20b"),    # protocol fallback
    ("nvidia", "z-ai/glm-5.3-flash"),    # protocol fallback
    ("gemini", "gemini-3.8-flash"),      # quota resets later
]
_clients: dict[str, OpenAI] = {}


def _client(provider: str) -> OpenAI:
    if provider not in _clients:
        key_var, base_url = _BACKENDS[provider]
        _clients[provider] = OpenAI(api_key=os.environ[key_var],
                                    base_url=base_url, timeout=60)
    return _clients[provider]


class TodoAgent:
    def __init__(self, backends: list | None = None):
        self.backends = backends or AGENT_BACKENDS

    def chat(self, messages: list[dict], tools: list | None = None) -> dict:
        """
        One agent step with backend failover.
        Returns {"reply", "tool_calls", "_backend"}. Raises RuntimeError
        only if EVERY backend fails.
        """
        errors = []
        for provider, model in self.backends:
            try:
                kwargs = {"model": model, "messages": messages, "temperature": 0.2}
                if tools:
                    kwargs["tools"] = tools
                resp = _client(provider).chat.completions.create(**kwargs)
                msg = resp.choices[0].message
                return {
                    "reply": msg.content or "",
                    "tool_calls": [tc.model_dump() for tc in (msg.tool_calls or [])],
                    "_backend": f"{provider}/{model}",
                }
            except Exception as e:
                errors.append(f"{provider}/{model} -> {type(e).__name__}: {str(e)[:150]}")
                time.sleep(2)
        raise RuntimeError("All agent backends failed:\n  " + "\n  ".join(errors))

    @staticmethod
    def execute_tool_calls(tool_calls: list[dict]) -> list[dict]:
        out = []
        for tc in tool_calls:
            fn = tc.get("function", {})
            result = run_tool(fn.get("name", ""), fn.get("arguments", ""))
            out.append({"role": "tool",
                        "tool_call_id": tc.get("id", "call_0"),
                        "content": result})
        return out