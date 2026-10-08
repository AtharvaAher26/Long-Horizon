"""
memory_store.py — The agent's memory (doc section 8.2, MVP version).
A JSON-backed list. Phase 4 (Compaction) will replace old items with a
structured summary and archive the raw ones.
"""
import json
from pathlib import Path

from models import MemoryItem


class MemoryStore:
    def __init__(self, path: str | Path = "data/memory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.items: list[MemoryItem] = []
        self.load()

    # --- core API ---
    def add(self, content: str, type: str = "observation", importance: float = 0.5) -> MemoryItem:
        item = MemoryItem(content=content, type=type, importance=importance)
        self.items.append(item)
        self.save()
        return item

    def recent(self, n: int = 10) -> list[MemoryItem]:
        return self.items[-n:]

    def search(self, keyword: str) -> list[MemoryItem]:
        k = keyword.lower()
        return [m for m in self.items if k in m.content.lower()]

    def count(self) -> int:
        return len(self.items)

    def working_context(self, n: int = 10) -> str:
        """Text block injected into the agent's prompt (used in Phase 5)."""
        lines = [f"[{m.type}] {m.content}" for m in self.recent(n)]
        return "\n".join(lines) if lines else "(memory empty)"

    # --- persistence ---
    def save(self) -> None:
        data = [json.loads(m.model_dump_json()) for m in self.items]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.items = [MemoryItem.model_validate(d) for d in raw]