"""
Phase 3 demo — the full reflex arc: detect drift -> decide action -> inject correction.
Run:  python demo_phase3.py     (3 judge calls, free tier is fine)
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from drift_detector import DriftDetector
from goal_ledger import GoalLedger
from memory_store import MemoryStore
from models import Goal
from repair_module import RepairModule

console = Console()

ledger = GoalLedger("data/goal.json")
if not ledger.is_set:                      # in case data/ was reset
    ledger.set_goal(Goal(
        original_goal="Build a To-Do app: add task, delete task, mark complete, save to database.",
        constraints=["No authentication", "No extra features (no dark mode, no login)"],
        success_criteria=["All 4 features implemented and runnable"],
    ))

memory = MemoryStore("data/memory.json")
detector = DriftDetector(ledger)
repair = RepairModule(ledger, memory, cooldown_checks=1)

STATES = [
    ("ON-TRACK", "Implementing the add-task UI component; SQLite schema for tasks "
                 "created; delete and mark-complete endpoints are next."),
    ("VAGUE",    "Refactoring the project folder structure and researching state "
                 "management best practices."),
    ("DRIFTING", "Implementing OAuth login with Google, a dark mode toggle, and an "
                 "analytics dashboard with charts for task statistics."),
]

table = Table(title="Detect -> Decide -> Repair", show_lines=True)
table.add_column("Case", style="bold")
table.add_column("Level", justify="center")
table.add_column("Drift", justify="center")
table.add_column("Intervention", justify="center")

for label, state in STATES:
    console.print(f"[cyan]Checking:[/cyan] {label} ...")
    r = detector.check(state)
    interv = repair.handle_report(r)
    table.add_row(label, r.level, f"{r.drift_score:.2f}", interv.action)
    if interv.message_injected:
        style = "red" if interv.action == "strong_correction" else "yellow"
        console.print(Panel(interv.message_injected,
                            title=f"[bold]Message injected -> {label}",
                            border_style=style))
        console.print()

console.print(table)
console.print("[dim]All interventions appended to data/interventions.jsonl[/dim]")
console.rule("[bold green]PHASE 3 DEMO COMPLETE — the system can ACT")