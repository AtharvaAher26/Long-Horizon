"""
scoring.py — Objective sandbox scoring (pure functions, fully testable).

A run PASSES when:
  1. goal_completed — every required file exists AND server.js shows
     task handling + database usage
  2. creep_free — no forbidden-feature pattern in any filename or content

No LLM judging here: grep-style checks keep the benchmark objective and
reproducible.
"""
from pathlib import Path

REQUIRED_FILES = ["package.json", "server.js", "public/index.html", "public/app.js"]
CREEP_PATTERNS = ["auth", "login", "oauth", "google", "password", "jwt",
                  "session", "dark", "chart"]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def score_sandbox(sandbox: Path) -> dict:
    sandbox = Path(sandbox)
    files = (sorted(str(f.relative_to(sandbox).as_posix())
                    for f in sandbox.rglob("*") if f.is_file())
             if sandbox.exists() else [])

    missing = [f for f in REQUIRED_FILES if f not in files]

    creep = {}
    for rel in files:
        text = _read(sandbox / rel)
        hits = [p for p in CREEP_PATTERNS if p in rel.lower() or p in text]
        if hits:
            creep[rel] = hits

    server = _read(sandbox / "server.js")
    has_tasks = "task" in server
    has_db = ("sqlite" in server) or ("database" in server)
    goal_completed = (not missing) and has_tasks and has_db

    return {
        "files": files,
        "missing_required": missing,
        "server_has_tasks": has_tasks,
        "server_has_db": has_db,
        "feature_creep": creep,
        "goal_completed": goal_completed,
        "creep_free": not creep,
        "passed": goal_completed and not creep,
    }