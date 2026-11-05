"""
conftest.py — makes the test suite hermetic: no network, no API keys.

compaction_engine.compact() calls providers.ask_llm, whose real failover
chain sleeps and times out against live APIs (the suite once took ~9 min).
Here ask_llm (as imported into compaction_engine) is replaced with a
deterministic stub that returns a fixed, valid summary — honouring the
validator contract exactly like the real ask_llm does. Everything else the
tests assert (protection rules, archiving, conservation counts, persistence)
runs against the real code, unstubbed.

No other module's LLM entry points are touched: drift/judge/agent paths are
not exercised by this suite.
"""
import json

import pytest

import compaction_engine

_CANNED_SUMMARY = json.dumps({
    "summary": "Stubbed summary of the compacted work history.",
    "key_decisions": ["Stub decision: kept the important items verbatim."],
    "current_progress": "Compaction completed against the stub LLM.",
    "open_tasks": ["Continue from the recent working context."],
})


def _stub_ask_llm(prompt, temperature=0.0, tag="", validator=None):
    """Deterministic stand-in for providers.ask_llm (compaction only)."""
    if validator is not None:
        return validator(_CANNED_SUMMARY)
    return _CANNED_SUMMARY


@pytest.fixture(autouse=True)
def _offline_llm(monkeypatch):
    monkeypatch.setattr(compaction_engine, "ask_llm", _stub_ask_llm)
