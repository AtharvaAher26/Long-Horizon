"""
Phase 1 demo — see the foundation with your eyes.
Run:  python demo_phase1.py      (run it TWICE to see the lock in action)
Reset anytime: delete the data/ folder.
"""
from rich.console import Console

from goal_ledger import GoalLedger, LedgerLockedError
from memory_store import MemoryStore
from models import Goal

console = Console()
ledger = GoalLedger("data/goal.json")
memory = MemoryStore("data/memory.json")

# 1) Goal Ledger (protected core)
if not ledger.is_set:
    console.rule("[cyan]Setting the goal (write-once)")
    ledger.set_goal(Goal(
        original_goal="Build a To-Do app: add task, delete task, mark complete, save to database.",
        constraints=["No authentication", "No extra features (no dark mode, no login)"],
        success_criteria=["All 4 features implemented and runnable"],
    ))
else:
    console.print("[yellow]Goal already locked (as designed) — showing ledger.[/yellow]")
console.print(ledger.goal_text())

# 2) Attempt to overwrite — must be blocked
console.rule("[cyan]Trying to overwrite the goal (should FAIL)")
try:
    ledger.set_goal(Goal(original_goal="Build a full e-commerce site instead"))
except LedgerLockedError as e:
    console.print(f"[green]Correctly blocked:[/green] {e}")

# 3) Memory Store
console.rule("[cyan]Memory Store")
if memory.count() == 0:
    memory.add("Created project structure (React + Node)", type="action", importance=0.6)
    memory.add("Decided: use SQLite for task storage", type="decision", importance=0.9)
    memory.add("Read about JWT auth for fun", type="observation", importance=0.2)
console.print(f"Memory items: {memory.count()}")
console.print(memory.working_context())

console.rule("[bold green]PHASE 1 DEMO COMPLETE — the foundation is alive")