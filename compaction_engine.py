"""
compaction_engine.py — Safe memory reduction (doc sections 8.5, 12).

What NEVER gets compacted:
  - the Goal Ledger (separate protected store — unreachable from here)
  - correction items and anything with importance >= KEEP_IMPORTANCE
  - the last RECENT_KEEP items (current working context)

What happens to compacted items:
  - replaced by ONE structured summary item (type="summary", importance=0.95)
  - raw items archived to data/archive.jsonl (searchable later, never lost)

LLM failure -> naive extractive fallback, so the agent loop is never blocked.
"""
import json
from pathlib import Path

from memory_store import MemoryStore
from models import MemoryItem
from providers import ask_llm

ARCHIVE_PATH = Path("data/archive.jsonl")

TRIGGER_COUNT = 30      # compact when memory exceeds this many items
RECENT_KEEP = 5         # newest items always stay
KEEP_IMPORTANCE = 0.9   # items at/above this survive verbatim

SUMMARY_PROMPT = """Summarize this AI agent's work history into a compact handover note.

Work history:
{history}

Reply with ONLY a JSON object, exactly these keys:
- "summary": one short paragraph of overall progress
- "key_decisions": list of important decisions made (strings)
- "current_progress": one sentence on where work stands
- "open_tasks": list of what remains (strings)
"""

REQUIRED_KEYS = {"summary"}


def _validate_summary(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON in reply: {text[:120]!r}")
    data = json.loads(text[start:end + 1])
    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"missing keys {missing}")
    data["summary"] = str(data["summary"]).strip()
    if not data["summary"]:
        raise ValueError("empty summary")
    return data


def naive_summary(items: list[MemoryItem]) -> dict:
    """Fallback when the LLM is unavailable: keep the gist, extractively."""
    bullets = [f"- [{i.type}] {i.content[:120]}" for i in items[-15:]]
    return {
        "summary": "LLM unavailable — extractive summary of " + str(len(items)) + " older items.",
        "key_decisions": bullets,
        "current_progress": "See items above.",
        "open_tasks": [],
    }


def render_summary(data: dict) -> str:
    lines = [data["summary"]]
    if data.get("key_decisions"):
        lines.append("Key decisions:")
        lines += [f"- {d}" for d in data["key_decisions"]]
    if data.get("current_progress"):
        lines.append(f"Current progress: {data['current_progress']}")
    if data.get("open_tasks"):
        lines.append("Open tasks:")
        lines += [f"- {t}" for t in data["open_tasks"]]
    return "\n".join(lines)


def split_for_compaction(items: list[MemoryItem]) -> tuple[list[MemoryItem], list[MemoryItem]]:
    """
    Pure function -> (keep, compact). Deterministic rules, fully testable.
    """
    cut = max(0, len(items) - RECENT_KEEP)
    keep, compact = [], []
    for idx, item in enumerate(items):
        protected = (
            idx >= cut                      # recent working context
            or item.importance >= KEEP_IMPORTANCE
            or item.type == "correction"
        )
        (keep if protected else compact).append(item)
    return keep, compact


class CompactionEngine:
    def __init__(self, memory: MemoryStore, archive_path: Path = ARCHIVE_PATH):
        self.memory = memory
        self.archive_path = Path(archive_path)

    def should_compact(self) -> bool:
        return self.memory.count() > TRIGGER_COUNT

    def compact_if_needed(self) -> dict | None:
        """Convenience for the Phase 5 loop: returns stats dict or None."""
        if not self.should_compact():
            return None
        return self.compact()

    def compact(self) -> dict:
        keep, to_compact = split_for_compaction(self.memory.items)
        if not to_compact:
            return {"before": self.memory.count(), "after": self.memory.count(),
                    "archived": 0, "used_llm": False, "compacted": False}

        # 1) summarize (LLM, fallback to naive)
        history = "\n".join(f"[{i.type}] (importance {i.importance}) {i.content}" for i in to_compact)
        try:
            data = ask_llm(SUMMARY_PROMPT.format(history=history), tag="compaction",
                           validator=_validate_summary)
            used_llm = True
        except RuntimeError:
            data = naive_summary(to_compact)
            used_llm = False

        # 2) archive raw items BEFORE replacing them
        self.archive_path.parent.mkdir(parents=True, exist_ok=True)
        with self.archive_path.open("a", encoding="utf-8") as f:
            for item in to_compact:
                f.write(json.dumps(item.model_dump()) + "\n")

        # 3) rebuild memory: kept items in original order + summary on top
        summary_item = MemoryItem(
            type="summary",
            content=render_summary(data),
            importance=0.95,
        )
        self.memory.items = keep + [summary_item]
        self.memory.save()

        return {"before": len(keep) + len(to_compact), "after": self.memory.count(),
                "archived": len(to_compact), "used_llm": used_llm, "compacted": True}