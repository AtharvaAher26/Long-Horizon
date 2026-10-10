"""
benchmark.py — Protected vs baseline (Phase 6).

Usage:
    python benchmark.py                 # 3 trials per condition
    $env:BENCH_TRIALS="5"; python benchmark.py   # 5 trials per condition

~30–60 min total on free tier (runs are paced automatically).
Each trial gets a fresh goal, fresh memory, empty sandbox, and its own
logs + sandbox snapshot under data/bench/<tag>/.
"""
import json
import os
import shutil
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from integrity_loop import fresh_session
from sandbox_tools import SANDBOX
from scoring import score_sandbox

console = Console()
RESULTS = Path("data/bench/results.json")
PACING_SECONDS = 15


def run_trials() -> list[dict]:
    trials = int(os.getenv("BENCH_TRIALS", "3"))
    rows = []
    for cond, protect in [("protected", True), ("baseline", False)]:
        for i in range(1, trials + 1):
            tag = f"{cond}_{i}"
            console.rule(f"[bold cyan]{cond} — trial {i}/{trials}")
            loop = fresh_session(protect=protect, tag=tag)
            result = loop.run()
            score = score_sandbox(SANDBOX)

            dest = Path("data/bench") / tag / "sandbox"
            if dest.exists():
                shutil.rmtree(dest)
            if SANDBOX.exists():
                shutil.copytree(SANDBOX, dest)

            rows.append({"tag": tag, "condition": cond,
                         "steps": result["steps"], "finished": result["finished"],
                         **score})
            console.print(f"  finished={result['finished']} steps={result['steps']} | "
                          f"completed={score['goal_completed']} "
                          f"creep_free={score['creep_free']} passed={score['passed']}")
            time.sleep(PACING_SECONDS)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return rows


def summarize(rows: list[dict]) -> None:
    table = Table(title="Benchmark — protected vs baseline")
    for col in ["condition", "trials", "completed", "creep-free", "PASSED", "avg steps"]:
        table.add_column(col)
    for cond in ["protected", "baseline"]:
        rs = [r for r in rows if r["condition"] == cond]
        n = len(rs) or 1
        table.add_row(cond, str(len(rs)),
                      f"{sum(r['goal_completed'] for r in rs)}/{len(rs)}",
                      f"{sum(r['creep_free'] for r in rs)}/{len(rs)}",
                      f"{sum(r['passed'] for r in rs)}/{len(rs)}",
                      f"{sum(r['steps'] for r in rs) / n:.1f}")
    console.print(table)


if __name__ == "__main__":
    rows = run_trials()
    summarize(rows)
    console.print(f"[dim]Details: {RESULTS} + per-trial sandboxes/logs in data/bench/[/dim]")