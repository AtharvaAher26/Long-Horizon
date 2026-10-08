"""
models.py — Data models for the whole system (Pydantic v2).
Single source of truth for Goal, MemoryItem, and DriftReport.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Goal(BaseModel):
    """The original mission — stored in the protected Goal Ledger."""
    original_goal: str
    constraints: list[str] = Field(default_factory=list)       # hard rules: scope, limits
    success_criteria: list[str] = Field(default_factory=list)  # how we know we're done
    created_at: str = Field(default_factory=utc_now)


class MemoryItem(BaseModel):
    """One entry in the agent's memory."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: str = Field(default_factory=utc_now)
    type: str = "observation"   # action | decision | observation | summary | correction
    content: str
    importance: float = 0.5     # 0.0-1.0 — used later by Compaction (Phase 4)
    embedding: Optional[list[float]] = None  # filled on demand by Drift Detector (Phase 2)


class DriftReport(BaseModel):
    """Output of the Drift Detector. Defined now, used in Phase 2."""
    drift_score: float              # 0.0 (aligned) - 1.0 (critical drift)
    level: str                      # LOW | MEDIUM | HIGH | CRITICAL
    problem_type: str = "None"
    reason: str = ""
    recommended_action: str = "continue"
    timestamp: str = Field(default_factory=utc_now)

class Intervention(BaseModel):
    """One repair-module decision, logged for evaluation."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: str = Field(default_factory=utc_now)
    trigger_drift_score: float
    trigger_level: str
    trigger_problem_type: str
    action: str                    # none | soft_correction | strong_correction | skipped_cooldown
    message_injected: str = ""
    notes: str = ""