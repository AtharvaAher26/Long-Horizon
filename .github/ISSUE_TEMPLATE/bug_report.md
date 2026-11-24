---
name: Bug report
about: Something in Long-Horizon didn't work as expected
title: "[Bug] "
labels: bug
---

**What happened**
A clear description of the bug.

**What you expected**
What Long-Horizon should have done instead.

**Component**
Which part is involved — Goal Ledger, drift detector, repair module,
compaction engine, memory store, sandbox tools, providers, or a demo?

**Steps to reproduce**
1. Command you ran (e.g. `pytest -v`, `python demo_phase3.py`, `python benchmark.py`)
2. Phase / test / demo scenario involved
3. Where it failed

**Integrity details**
- Was a drift verdict wrong — missed real drift, or a false alarm on a faithful agent?
- Did compaction drop, alter, or fail to archive something it shouldn't have?
- Was the Goal Ledger touched in any way? (It is write-once — any change is critical.)

**Environment**
- OS:
- Python version (`python --version`):
- Keys present? (GEMINI_API_KEY / NVIDIA_API_KEY — say which, never paste the key itself)

**Sample output**
Paste the relevant output or log here — remove API keys and anything
private first. If a verdict looks wrong, include the state the detector
saw and the verdict it returned.
