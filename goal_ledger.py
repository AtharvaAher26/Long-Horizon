"""
goal_ledger.py — The Protected Core (doc section 8.1).
Write-once storage for the original goal. Once set, it CANNOT be overwritten
in the MVP. That is the whole point: the goal must survive summarization,
drift, and long runs.
"""
from pathlib import Path

from models import Goal


class LedgerNotSetError(Exception):
    """Reading the goal before it was set."""


class LedgerLockedError(Exception):
    """Trying to overwrite an already-set goal."""


class GoalLedger:
    def __init__(self, path: str | Path = "data/goal.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._goal: Goal | None = None
        self._load()

    @property
    def is_set(self) -> bool:
        return self._goal is not None

    def set_goal(self, goal: Goal) -> None:
        if self._goal is not None:
            raise LedgerLockedError(
                "Goal Ledger is locked — the original goal cannot be overwritten. "
                "(A user-initiated goal change = start a NEW session.)"
            )
        self._goal = goal
        self._save()

    def get_goal(self) -> Goal:
        if self._goal is None:
            raise LedgerNotSetError("No goal set yet. Call set_goal() first.")
        return self._goal

    def goal_text(self) -> str:
        """Full goal as one block — this is what Phase 2 embeds and compares against."""
        g = self.get_goal()
        lines = [f"GOAL: {g.original_goal}"]
        if g.constraints:
            lines.append("CONSTRAINTS: " + "; ".join(g.constraints))
        if g.success_criteria:
            lines.append("SUCCESS CRITERIA: " + "; ".join(g.success_criteria))
        return "\n".join(lines)

    # --- persistence ---
    def _save(self) -> None:
        self.path.write_text(self._goal.model_dump_json(), encoding="utf-8")

    def _load(self) -> None:
        if self.path.exists():
            self._goal = Goal.model_validate_json(self.path.read_text(encoding="utf-8"))