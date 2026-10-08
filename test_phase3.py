"""
Phase 3 tests — repair logic only. No API calls.
Run:  pytest test_phase3.py -v
"""
import json

from goal_ledger import GoalLedger
from memory_store import MemoryStore
from models import DriftReport, Goal
from repair_module import RepairModule


def make_env(tmp_path):
    ledger = GoalLedger(tmp_path / "goal.json")
    ledger.set_goal(Goal(
        original_goal="Build a To-Do app with add, delete, complete, and DB storage.",
        constraints=["No authentication", "No extra features"],
        success_criteria=["All 4 features work"],
    ))
    memory = MemoryStore(tmp_path / "memory.json")
    repair = RepairModule(ledger, memory, cooldown_checks=1,
                          log_path=tmp_path / "interventions.jsonl")
    return memory, repair


def report(level, score=0.6, problem="Feature Creep", reason="adding auth"):
    return DriftReport(drift_score=score, level=level, problem_type=problem,
                       reason=reason, recommended_action="x")


def test_low_no_intervention(tmp_path):
    _, repair = make_env(tmp_path)
    interv = repair.handle_report(report("LOW", score=0.1, problem="None"))
    assert interv.action == "none"
    assert interv.message_injected == ""


def test_medium_soft_correction(tmp_path):
    _, repair = make_env(tmp_path)
    interv = repair.handle_report(report("MEDIUM"))
    assert interv.action == "soft_correction"
    assert "REMINDER" in interv.message_injected
    assert "No authentication" in interv.message_injected   # ledger text injected verbatim


def test_high_strong_correction(tmp_path):
    _, repair = make_env(tmp_path)
    interv = repair.handle_report(report("HIGH"))
    assert interv.action == "strong_correction"
    assert "STOP" in interv.message_injected
    assert "Feature Creep" in interv.message_injected


def test_critical_also_strong(tmp_path):
    _, repair = make_env(tmp_path)
    assert repair.handle_report(report("CRITICAL")).action == "strong_correction"


def test_strong_correction_writes_memory(tmp_path):
    memory, repair = make_env(tmp_path)
    repair.handle_report(report("CRITICAL"))
    assert memory.count() == 1
    item = memory.recent(1)[0]
    assert item.type == "correction"
    assert item.importance == 1.0


def test_cooldown_blocks_then_releases(tmp_path):
    _, repair = make_env(tmp_path)
    assert repair.handle_report(report("HIGH")).action == "strong_correction"
    assert repair.handle_report(report("HIGH")).action == "skipped_cooldown"
    assert repair.handle_report(report("HIGH")).action == "strong_correction"


def test_interventions_logged(tmp_path):
    p = tmp_path / "interventions.jsonl"
    _, repair = make_env(tmp_path)
    repair.handle_report(report("LOW", score=0.1, problem="None"))
    repair.handle_report(report("MEDIUM"))
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[1])["action"] == "soft_correction"