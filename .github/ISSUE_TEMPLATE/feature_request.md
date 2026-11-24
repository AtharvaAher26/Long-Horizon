---
name: Feature request
about: Suggest an idea for Long-Horizon
title: "[Feature] "
labels: enhancement
---

**Problem**
What gap does this solve? (A drift pattern the detector can't catch
today, a memory failure mode with no repair, an agent setup the layer
can't wrap.)

**Proposed change**
What should Long-Horizon do differently? Be concrete: a new signal in
the drift detector, a new repair action, a compaction rule, a provider.

**Scope note**
Long-Horizon's ground rules (see CONTRIBUTING.md) are not negotiable:
the Goal Ledger is write-once, the watcher shares no state with the
watched, compaction never drops protected items, and the test suite
stays hermetic — offline, no API keys. A feature that breaks one of
those is a regression, not an improvement. If your idea needs an LLM
call in a tested path, say how it stays stub-able.

**Alternatives considered**
Anything else you tried, or a simpler version of the same idea.
