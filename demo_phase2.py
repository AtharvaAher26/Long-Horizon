"""
Phase 2 demo — one goal, three agent states, three verdicts.
Run:  python demo_phase2.py     (makes ~4 embedding calls + 3 judge calls)
"""
from rich.console import Console
from rich.table import Table

from drift_detector import DriftDetector
from goal_ledger import GoalLedger

console = Console()
ledger = GoalLedger("data/goal.json")     # the To-Do goal you locked in Phase 1
detector = DriftDetector(ledger)
console.print("[dim]Goal embedded once at startup — checks are cheap from here.[/dim]\n")

STATES = [
    ("ON-TRACK", "Implementing the add-task UI component; SQLite schema for tasks "
                 "created; delete and mark-complete endpoints are next."),
    ("VAGUE",    "Refactoring the project folder structure and researching state "
                 "management best practices."),
    ("DRIFTING", "Implementing OAuth login with Google, a dark mode toggle, and an "
                 "analytics dashboard with charts for task statistics."),
]

table = Table(title="Drift Detector — live verdicts", show_lines=True)
table.add_column("Case", style="bold")
table.add_column("Drift", justify="center")
table.add_column("Level", justify="center")
table.add_column("Problem type")
table.add_column("Reason")
table.add_column("Action")

for label, state in STATES:
    console.print(f"[cyan]Checking:[/cyan] {label} ...")
    r = detector.check(state)
    color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "dark_orange", "CRITICAL": "red"}[r.level]
    table.add_row(label, f"{r.drift_score:.2f}", f"[{color}]{r.level}[/{color}]",
                  r.problem_type, r.reason, r.recommended_action)

console.print(table)
console.print(f"\n[dim]All checks appended to data/drift_log.jsonl (used in Phase 6).[/dim]")
console.rule("[bold green]PHASE 2 DEMO COMPLETE — the system can THINK")