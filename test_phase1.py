"""
Phase 1 tests — pure local, no API calls, no network.
Run:  pytest test_phase1.py -v
"""
import pytest

from goal_ledger import GoalLedger, LedgerLockedError, LedgerNotSetError
from memory_store import MemoryStore
from models import DriftReport, Goal


def make_goal() -> Goal:
    return Goal(
        original_goal="Build a To-Do app with add, delete, complete, and DB storage.",
        constraints=["No authentication", "No extra features"],
        success_criteria=["All 4 features work", "Code runs without errors"],
    )


# ---------- Goal Ledger ----------

def test_goal_set_and_get(tmp_path):
    ledger = GoalLedger(tmp_path / "goal.json")
    assert ledger.is_set is False
    with pytest.raises(LedgerNotSetError):
        ledger.get_goal()
    ledger.set_goal(make_goal())
    assert ledger.is_set is True


def test_goal_is_locked_after_set(tmp_path):
    ledger = GoalLedger(tmp_path / "goal.json")
    ledger.set_goal(make_goal())
    with pytest.raises(LedgerLockedError):
        ledger.set_goal(Goal(original_goal="totally different goal"))


def test_goal_persists_across_restart(tmp_path):
    p = tmp_path / "goal.json"
    GoalLedger(p).set_goal(make_goal())
    ledger2 = GoalLedger(p)  # fresh instance = simulated restart
    assert ledger2.is_set is True
    assert "To-Do app" in ledger2.goal_text()


def test_goal_text_includes_constraints(tmp_path):
    ledger = GoalLedger(tmp_path / "goal.json")
    ledger.set_goal(make_goal())
    text = ledger.goal_text()
    assert "CONSTRAINTS" in text and "No authentication" in text


# ---------- Memory Store ----------

def test_add_and_recent(tmp_path):
    store = MemoryStore(tmp_path / "memory.json")
    for i in range(20):
        store.add(content=f"action number {i}", type="action")
    assert store.count() == 20
    recent = store.recent(5)
    assert len(recent) == 5
    assert recent[-1].content == "action number 19"   # newest last
    assert recent[0].content == "action number 15"


def test_search(tmp_path):
    store = MemoryStore(tmp_path / "memory.json")
    store.add("wrote database.py module")
    store.add("added dark mode styling")
    store.add("fixed delete task bug")
    hits = store.search("database")
    assert len(hits) == 1 and "database" in hits[0].content


def test_memory_persists(tmp_path):
    p = tmp_path / "memory.json"
    MemoryStore(p).add("checkpoint one", type="decision", importance=0.9)
    store2 = MemoryStore(p)  # simulated restart
    assert store2.count() == 1
    assert store2.recent(1)[0].type == "decision"
    assert store2.recent(1)[0].importance == 0.9


def test_working_context(tmp_path):
    store = MemoryStore(tmp_path / "memory.json")
    assert store.working_context() == "(memory empty)"
    store.add("step A")
    store.add("step B")
    assert "step A" in store.working_context() and "step B" in store.working_context()


def test_drift_report_model():
    r = DriftReport(drift_score=0.75, level="HIGH", problem_type="Feature Creep",
                    reason="adding auth", recommended_action="strong_repair")
    assert r.timestamp  # auto-filled correctly