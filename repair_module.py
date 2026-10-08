"""
repair_module.py — The hands (doc sections 8.6, 11).

Mapping from drift level to action (doc section 10/11):
    LOW      -> no intervention
    MEDIUM   -> soft correction  (reminder with the protected goal text)
    HIGH/CRITICAL -> strong correction (STOP message + correction memory written)

Correction messages are built FROM THE GOAL LEDGER TEXT ONLY — the ledger is
the single source of truth, never an LLM paraphrase of it.

Cooldown: after a correction fires, the next `cooldown_checks` reports are
suppressed (hysteresis) so a drifting agent isn't spammed every check.
"""
import json
from pathlib import Path

from goal_ledger import GoalLedger
from memory_store import MemoryStore
from models import DriftReport, Intervention

DEFAULT_LOG = Path("data/interventions.jsonl")


class RepairModule:
    def __init__(self, ledger: GoalLedger, memory: MemoryStore,
                 cooldown_checks: int = 2, log_path: Path = DEFAULT_LOG):
        self.ledger = ledger
        self.memory = memory
        self.cooldown_checks = cooldown_checks
        self.log_path = Path(log_path)
        self._quiet_checks = cooldown_checks   # ready to fire immediately at startup

    # ---------------- message builders (pure, testable) ----------------

    def _soft_message(self, report: DriftReport) -> str:
        return (
            "REMINDER — POSSIBLE DRIFT FROM ORIGINAL GOAL\n\n"
            f"{self.ledger.goal_text()}\n\n"
            f"Detected: {report.problem_type} — {report.reason}\n"
            "Continue, but refocus on the original goal and its constraints."
        )

    def _strong_message(self, report: DriftReport) -> str:
        return (
            "STOP — STRONG CORRECTION REQUIRED\n\n"
            f"{self.ledger.goal_text()}\n\n"
            f"Detected problem: {report.problem_type}\n"
            f"Why: {report.reason}\n\n"
            "Required action:\n"
            "1. Stop the off-track work described above.\n"
            "2. Continue ONLY with what the original goal and its constraints require."
        )

    # ------------------------- main entry ------------------------------

    def handle_report(self, report: DriftReport) -> Intervention:
        fire_allowed = self._quiet_checks >= self.cooldown_checks

        if report.level == "LOW":
            self._quiet_checks += 1
            action, message = "none", ""
            notes = "agent aligned — no intervention"

        elif not fire_allowed:
            self._quiet_checks += 1
            action, message = "skipped_cooldown", ""
            notes = (f"drift detected but suppressed "
                     f"({self._quiet_checks}/{self.cooldown_checks} checks since last intervention)")

        else:
            strong = report.level in ("HIGH", "CRITICAL")
            action = "strong_correction" if strong else "soft_correction"
            message = self._strong_message(report) if strong else self._soft_message(report)
            notes = f"{action} injected into agent context"
            self._quiet_checks = 0

            if strong:
                # High-importance memory so the correction survives compaction
                self.memory.add(
                    content=f"CORRECTION ({report.problem_type}): {report.reason}. "
                            f"Refocus on the original goal.",
                    type="correction",
                    importance=1.0,
                )

        interv = Intervention(
            trigger_drift_score=report.drift_score,
            trigger_level=report.level,
            trigger_problem_type=report.problem_type,
            action=action,
            message_injected=message,
            notes=notes,
        )
        self._log(interv)
        return interv

    def _log(self, interv: Intervention) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(interv.model_dump()) + "\n")