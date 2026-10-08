"""
drift_detector.py — The brain (doc sections 6.3, 8.4, 10).

Two independent signals, combined into one drift verdict:

  Signal #1  Embeddings: cosine similarity between the protected goal text
             (embedded ONCE at startup) and a summary of the agent's
             current state.
  Signal #2  LLM-as-Judge: alignment 0-1 + problem type + reason.

CALIBRATION — thresholds come from Phase 0 validation pairs measured with
gemini-embedding-001:
    drifting state  -> cosine 0.557
    aligned state   -> cosine 0.751
SIM_LOW / SIM_HIGH bracket that band; anything below LOW = max drift signal,
anything above HIGH = fully aligned signal.
"""
import json
from pathlib import Path

from embeddings import cosine, embed
from goal_ledger import GoalLedger
from models import DriftReport
from providers import ask_judge

# ---- calibration constants (from YOUR Phase 0 measurements) ----
SIM_LOW = 0.60    # at/below this similarity -> drift signal = 0.0
SIM_HIGH = 0.75   # at/above this similarity -> drift signal = 1.0

EMBEDDING_WEIGHT = 0.4   # cheap but noisy
JUDGE_WEIGHT = 0.6       # slower but understands intent

DRIFT_LOG = Path("data/drift_log.jsonl")


# ---------------- pure functions (unit-testable, no network) ----------------

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def sim_to_signal(sim: float) -> float:
    """Raw cosine -> 0-1 alignment signal, calibrated to the Phase 0 band."""
    return clamp01((sim - SIM_LOW) / (SIM_HIGH - SIM_LOW))


def level_for(drift_score: float) -> str:
    """Doc section 10 bands."""
    if drift_score < 0.30:
        return "LOW"
    if drift_score < 0.55:
        return "MEDIUM"
    if drift_score < 0.75:
        return "HIGH"
    return "CRITICAL"


def action_for(level: str) -> str:
    return {
        "LOW": "continue",
        "MEDIUM": "soft_correction: re-inject goal into context",
        "HIGH": "strong_repair: force focus back to goal",
        "CRITICAL": "strong_repair now (rollback unavailable in MVP)",
    }[level]


def combine(embedding_signal: float, judge_alignment: float | None) -> tuple[float, str]:
    """
    Merge signals -> (drift_score, level).
    With judge: weighted mix. Without (degraded mode): embedding signal only.
    drift_score = 1.0 - overall alignment.  0 = perfect, 1 = totally lost.
    """
    if judge_alignment is None:
        alignment = clamp01(embedding_signal)
    else:
        alignment = EMBEDDING_WEIGHT * clamp01(embedding_signal) + JUDGE_WEIGHT * clamp01(judge_alignment)
    drift = 1.0 - alignment
    return drift, level_for(drift)


# ------------------------------ the detector ------------------------------

class DriftDetector:
    def __init__(self, ledger: GoalLedger):
        self.goal_text = ledger.goal_text()      # raises LedgerNotSetError if empty
        self.goal_embedding = embed(self.goal_text)   # embedded ONCE — reuse every check

    def check(self, current_state: str, use_judge: bool = True) -> DriftReport:
        sim = cosine(embed(current_state), self.goal_embedding)
        e_signal = sim_to_signal(sim)

        judge = None
        if use_judge:
            try:
                judge = ask_judge(goal=self.goal_text, state=current_state)
            except RuntimeError:
                judge = None    # all providers busy -> degraded mode

        a = clamp01(judge["alignment"]) if judge else None
        drift, level = combine(e_signal, a)

        report = DriftReport(
            drift_score=round(drift, 3),
            level=level,
            problem_type=judge["problem_type"] if judge else ("None" if level == "LOW" else "Embedding-only signal"),
            reason=judge["reason"] if judge else f"cosine similarity {sim:.3f} (judge unavailable)",
            recommended_action=action_for(level),
        )

        DRIFT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with DRIFT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "state": current_state[:200],
                "similarity": round(sim, 3),
                "judge_alignment": a,
                "provider": judge.get("_provider") if judge else None,
                **report.model_dump(),
            }) + "\n")

        return report