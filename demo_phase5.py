"""
Phase 5 demo — the full story in one command:
  protected agent WITH the integrity layer, distraction injected mid-run.
Run:  python demo_phase5.py     (the longest run of the project — grab coffee)
"""
from rich.console import Console

from integrity_loop import fresh_session

console = Console()
loop = fresh_session()
result = loop.run()

console.rule("[bold cyan]Final sandbox contents")
from sandbox_tools import list_files
console.print(list_files())

console.rule("[bold green]DEMO COMPLETE")
console.print("[bold]Now check the evidence:[/bold]")
console.print("  data/run_log.jsonl           — step-by-step what happened")
console.print("  data/interventions.jsonl     — every correction the layer fired")
console.print("  data/drift_log.jsonl         — every drift verdict with scores")