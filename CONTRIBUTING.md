# Contributing to Long-Horizon

Long-Horizon is a memory & state integrity layer for long-running AI
agents: a write-once **Goal Ledger**, continuous **drift detection**,
automatic **repair**, and **safe compaction**. It doesn't just store an
agent's memory — it keeps checking that the memory, the goal, and the
agent's current state still agree, and fixes them when they don't.

## Setup

Requires Python 3.11+.

```bash
git clone https://github.com/AtharvaAher26/Long-Horizon.git
cd Long-Horizon
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Keys:** the test suite needs **no keys and no network** (see Tests).
The demos and the benchmark call live models, so create a `.env` with
free-tier keys:

```env
GEMINI_API_KEY=<your-key>
NVIDIA_API_KEY=<your-key>
```

Never commit `.env` or a key — `.env` is for your machine only.

## Tests

```bash
pytest -v
```

52 tests across 6 suites (`test_phase1.py` … `test_phase6.py`), and
the suite is **hermetic**: `conftest.py` stubs the one LLM call the
compaction path makes, so the whole run is offline, key-free, and
finishes in about half a second. Everything else — protection rules,
archiving, conservation counts, persistence, the sandbox path jail —
runs against the real code, unstubbed.

The split is deliberate: pure core (scoring math, calibration mapping,
compaction selection) tested offline in milliseconds; effectful shell
(persistence, providers) exercised by the demos.

## Demos

```bash
python demo_phase1.py   # goal gets locked — run twice, watch the lock hold
python demo_phase2.py   # drift detector: live verdicts on 3 scenarios
python demo_phase3.py   # detect → decide → inject correction (full reflex arc)
python demo_phase4.py   # safe compaction: 44 → 8 items, ledger untouched
python demo_phase5.py   # agent builds an app, gets distracted, recovers
python benchmark.py     # full benchmark run (~30–60 min, paced, needs keys)
```

## Ground rules

These are load-bearing — a change that breaks one is a regression:

- **The Goal Ledger is write-once.** The user's goal is frozen and
  embedded once. Compaction, repair, and drift correction never rewrite
  it — if code wants to edit the ledger, the answer is no.
- **The watcher shares no state with the watched.** The integrity layer
  sits between the agent and its memory and observes from outside; it
  must never reach into the agent's internals or share mutable state
  with it. That's what lets the same layer wrap any agent unchanged.
- **Compaction protection rules are sacred.** Protected items (ledger,
  constraints, key decisions) are never compacted away, and compaction
  archives rather than deletes. Conservation counts must still add up.
- **Tests stay hermetic.** New tests must run offline with no API keys.
  If a path needs an LLM, stub it at the seam `conftest.py` uses —
  don't let a test sleep, time out, or call a live API.
- **Benchmark numbers only move from a real run.** The figures in the
  README come from `benchmark.py`; never edit them by hand or from a
  partial run.
- **No keys in the repo.** Not in code, not in test fixtures, not in
  issues or PRs.

## Pull requests

- One focused change per PR, with a clear title and a short description
  of what changed and why.
- Run `pytest -v` and say so in the PR; if you touched a demo path, say
  which demos you ran (and with which provider).
- If your change touches drift verdicts, repair behaviour, or
  compaction, explain how the ground rules above still hold.
