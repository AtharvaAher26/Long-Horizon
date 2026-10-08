"""
Phase 4 tests — compaction selection logic + storage mechanics. No API calls.
Run:  pytest test_phase4.py -v
"""
import json

from compaction_engine import (_validate_summary, naive_summary,
                               render_summary, split_for_compaction)
from goal_ledger import GoalLedger
from memory_store import MemoryStore
from models import Goal
from pytest import approx


def make_items(n_low=25, n_high=2, n_correction=1):
    items = []
    for i in range(n_low):
        items.append(_item(f"low priority step {i}", importance=0.4))
    for i in range(n_high):
        items.append(_item(f"key decision {i}", importance=0.95))
    for i in range(n_correction):
        items.append(_item("CORRECTION: stop adding auth", type="correction", importance=1.0))
    return items


def _item(content, type="observation", importance=0.5):
    from models import MemoryItem
    return MemoryItem(content=content, type=type, importance=importance)


# ---------- split_for_compaction (the protection rules) ----------

def test_high_importance_survives():
    items = make_items()
    keep, compact = split_for_compaction(items)
    kept_types = [i.type for i in keep]
    assert kept_types.count("correction") == 1
    assert any(i.importance == 0.95 for i in keep)

def test_old_low_importance_is_compacted():
    items = make_items(n_low=25, n_high=0, n_correction=0)
    keep, compact = split_for_compaction(items)
    assert len(compact) == 25 - 5          # all but the 5 most recent
    assert all(i.importance < 0.9 for i in compact)

def test_recent_items_always_survive():
    items = make_items(n_low=10, n_high=0, n_correction=0)
    keep, compact = split_for_compaction(items)
    assert len(compact) == 5
    assert keep[-5:] == items[-5:]         # newest 5, in order

def test_empty_memory_is_safe():
    keep, compact = split_for_compaction([])
    assert keep == [] and compact == []


# ---------- summary rendering & validation ----------

def test_validator_accepts_good_json():
    data = _validate_summary('```json {"summary": "did stuff", "key_decisions": ["sqlite"]} ```')
    assert data["summary"] == "did stuff"

def test_validator_rejects_garbage():
    import pytest
    with pytest.raises(ValueError):
        _validate_summary("no json here at all")
    with pytest.raises(ValueError):
        _validate_summary('{"wrong": 1}')

def test_render_summary_includes_sections():
    text = render_summary({"summary": "Built UI.", "key_decisions": ["Use SQLite"],
                           "current_progress": "Half done.", "open_tasks": ["Delete task"]})
    assert "Built UI." in text and "SQLite" in text and "Delete task" in text

def test_naive_summary_fallback():
    data = naive_summary([_item("step one"), _item("step two")])
    assert "step two" in render_summary(data)


# ---------- full compaction against a real MemoryStore ----------

def test_full_compaction_end_to_end(tmp_path):
    from compaction_engine import CompactionEngine
    ledger = GoalLedger(tmp_path / "goal.json")
    ledger.set_goal(Goal(original_goal="Build a To-Do app."))
    memory = MemoryStore(tmp_path / "memory.json")
    for i in range(40):
        memory.add(f"fake action {i}", importance=0.4)
    memory.add("CORRECTION: refocus", type="correction", importance=1.0)

    engine = CompactionEngine(memory, archive_path=tmp_path / "archive.jsonl")
    assert engine.should_compact() is True

    before = memory.count()
    stats = engine.compact()
    assert stats["before"] == before and stats["after"] < 15
    # conservation: before = archived + kept_raw;  after = kept_raw + 1 summary
    kept_raw = stats["before"] - stats["archived"]
    assert stats["after"] == kept_raw + 1
    assert stats["archived"] == before - 5            # exactly the 5 recent survived raw

    # corrections survive verbatim
    contents = [m.content for m in memory.items]
    assert "CORRECTION: refocus" in contents
    # one summary item on top
    assert memory.items[-1].type == "summary"
    assert memory.items[-1].importance == 0.95

    # archive holds every compacted raw item, valid JSONL
    lines = (tmp_path / "archive.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == stats["archived"]
    json.loads(lines[0])                    # parses

    # ledger untouched by compaction
    assert "To-Do app" in ledger.goal_text()

    # memory persistence rewritten correctly
    assert MemoryStore(tmp_path / "memory.json").count() == stats["after"]

def test_no_compaction_below_threshold(tmp_path):
    from compaction_engine import CompactionEngine
    memory = MemoryStore(tmp_path / "memory.json")
    memory.add("one small action")
    engine = CompactionEngine(memory, archive_path=tmp_path / "archive.jsonl")
    assert engine.compact_if_needed() is None
    assert not (tmp_path / "archive.jsonl").exists()