"""
Phase 4 demo — memory bloat -> safe compaction, ledger untouched.
Run:  python demo_phase4.py    (1 LLM call; falls back to naive if providers are busy)
"""
import random

from rich.console import Console
from rich.panel import Panel

from compaction_engine import CompactionEngine
from goal_ledger import GoalLedger
from memory_store import MemoryStore

console = Console()

ledger = GoalLedger("data/goal.json")
memory = MemoryStore("data/memory.json")

if memory.count() < 30:                        # seed the bloat (idempotent demo)
    console.print("[cyan]Seeding 40 realistic memories...[/cyan]")
    topics = [
        "Created {c} component in src/components",
        "Wrote SQLite schema for tasks table",
        "Debugged fetch call returning 404",
        "Added form validation for task input",
        "Reviewed CSS layout for task list",
        "Refactored api/tasks.js helper functions",
        "Tested mark-complete flow manually",
        "Read docs about React useEffect cleanup",
    ]
    random.seed(42)
    for i in range(40):
        memory.add(random.choice(topics).format(c=i), type="action", importance=0.4)

console.rule("[cyan]Before compaction")
console.print(f"Memory items: [bold]{memory.count()}[/bold]")
console.print("[dim]Goal ledger: " + ledger.goal_text().splitlines()[0] + "[/dim]")

engine = CompactionEngine(memory)
stats = engine.compact_if_needed() or engine.compact()

console.rule("[cyan]After compaction")
console.print(f"Memory items: [bold]{stats['after']}[/bold]  "
              f"(was {stats['before']}, archived {stats['archived']}, "
              f"LLM used: {stats['used_llm']})")
console.print(Panel(memory.items[-1].content, title="The summary item",
                    border_style="green"))
console.print("[dim]Raw items safely in data/archive.jsonl — searchable later, never deleted.[/dim]")
console.print("[dim]Goal ledger untouched: " + ledger.goal_text().splitlines()[0] + "[/dim]")
console.rule("[bold green]PHASE 4 DEMO COMPLETE — the system can FORGET SAFELY")