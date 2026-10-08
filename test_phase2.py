"""
Phase 2 tests — the scoring math ONLY. No API calls, runs in milliseconds.
Run:  pytest test_phase2.py -v
"""
import pytest

from drift_detector import action_for, combine, level_for, sim_to_signal


# ---- calibration: YOUR Phase 0 measurements must map correctly ----

def test_calibration_drifting_score():
    assert sim_to_signal(0.557) == pytest.approx(0.0)   # measured drift -> max drift signal

def test_calibration_aligned_score():
    assert sim_to_signal(0.751) == pytest.approx(1.0)   # measured aligned -> fully aligned

def test_calibration_midpoint():
    assert sim_to_signal(0.675) == pytest.approx(0.5)

def test_calibration_clamps_extremes():
    assert sim_to_signal(0.10) == 0.0
    assert sim_to_signal(0.99) == 1.0


# ---- combination math ----

def test_aligned_case_is_low():
    drift, level = combine(embedding_signal=0.9, judge_alignment=0.95)
    assert level == "LOW" and drift < 0.15

def test_feature_creep_case_is_critical():
    # judge says 0.2 (like our Phase 0 live test), embedding says max drift
    drift, level = combine(embedding_signal=0.0, judge_alignment=0.2)
    assert level == "CRITICAL" and drift == pytest.approx(0.88)

def test_weights_are_applied():
    # 0.4*1.0 + 0.6*0.5 = 0.7 alignment -> drift 0.30 -> exactly MEDIUM boundary
    drift, level = combine(embedding_signal=1.0, judge_alignment=0.5)
    assert drift == pytest.approx(0.30) and level == "MEDIUM"

def test_monotonic_more_drift_when_judge_worse():
    d1, _ = combine(0.5, 0.9)
    d2, _ = combine(0.5, 0.3)
    assert d2 > d1

def test_degraded_mode_uses_embedding_only():
    drift, level = combine(embedding_signal=1.0, judge_alignment=None)
    assert drift == pytest.approx(0.0) and level == "LOW"
    drift, level = combine(embedding_signal=0.0, judge_alignment=None)
    assert drift == pytest.approx(1.0) and level == "CRITICAL"


# ---- level bands (doc section 10 table) ----

def test_level_bands():
    assert level_for(0.0) == "LOW"
    assert level_for(0.30) == "MEDIUM"
    assert level_for(0.54) == "MEDIUM"
    assert level_for(0.55) == "HIGH"
    assert level_for(0.74) == "HIGH"
    assert level_for(0.75) == "CRITICAL"
    assert level_for(1.0) == "CRITICAL"

def test_action_mapping_matches_doc():
    assert action_for("LOW") == "continue"
    assert "soft_correction" in action_for("MEDIUM")
    assert "strong_repair" in action_for("HIGH")