Long-Horizon Agent Memory & State Integrity Layer
Not just memory storage — a system that keeps long-running AI agents correct, focused, and consistent over hours-long tasks.

Status: Core integrity layer complete and fully tested (37/37 tests) · Agent-in-the-loop demo & benchmark in progress

1. The Problem
   AI agents that work for a long time (hours or days) don't fail only because models are imperfect — they fail because memory and state are poorly managed:

Failure Mode Description
Context Rot Reasoning quality degrades as history grows, even before the context window is full
Memory / Semantic Drift Summarization or rewriting slowly corrupts facts, goals, constraints
Goal Drift Agent gradually abandons the original objective and chases intermediate outputs
State Corruption Working memory becomes inconsistent (contradictory facts, lost subgoals)
Governance Decay Safety constraints and policies get silently dropped during compaction
Compounding Errors One early mistake cascades because later decisions rely on corrupted state
Key insight: bigger context windows do not solve these problems. The issues are architectural — how memory is managed — not model capacity.

2. The Idea
   Current memory systems (full-history replay, RAG, MemGPT-style hierarchies, graph memory) are good at storing information — and weak at keeping the agent correct.

This project treats memory integrity as a first-class concern:

Store memory → Continuously check it → Detect problems → Fix them.

Capability Current systems This project
Store / retrieve memory ✅ ✅
Continuously check correctness weak / missing ✅ strong focus
Detect goal drift weak ✅ multi-signal detector
Automatically repair problems almost none ✅ core feature
Protect the original goal weak ✅ write-once Goal Ledger
Safe compaction lossy ✅ protection rules + archive 3. Architecture
flowchart TB U[User Goal] --> GL subgraph LAYER [Memory & State Integrity Layer] GL[Goal Ledger — write-once, protected core] MS[Memory Store — hierarchical, JSON-backed] DD[Drift Detector — embeddings + LLM-as-Judge] RM[Repair Module — soft / strong correction, cooldown] CE[Compaction Engine — safe summarization + archive] end A[Agent — LLM + tools] E[Embedding model] J[LLM Judge — multi-provider failover] A -- actions & results --> MS MS --> DD GL -- original goal, embedded once --> DD E --> DD J --> DD DD -- drift report --> RM RM -- correction injected into context --> A MS -- grows --> CE CE -- structured summary, raw items archived --> MS
The reflex arc
goal set (frozen) → agent works → memory records everything → every N steps: drift check (2 signals, weighted) → LOW: continue · MEDIUM: remind goal · HIGH/CRITICAL: strong correction → memory too large? safe compaction (ledger + corrections protected) 4. Components
4.1 Goal Ledger — the protected core
Write-once storage for the original goal, hard constraints, and success criteria. Once set, it cannot be overwritten (a user-initiated goal change = a new session). Every integrity check compares against this — it's embedded once at startup, so checks stay cheap. Persisted to disk; survives restarts.

4.2 Memory Store
JSON-backed memory with typed items (action, decision, observation, correction, summary), importance scores (0–1), and persistence. Provides the working context injected into the agent's prompt.

4.3 Drift Detector — two independent signals
Signal #1 — Embedding similarity. Cosine similarity between the protected goal text and a summary of the agent's current state, calibrated on validation pairs measured with gemini-embedding-001:

Validation pair Measured cosine
Goal vs. drifting state 0.557
Goal vs. aligned state 0.751
These bracket the band: similarity is linearly mapped to a 0–1 alignment signal (SIM_LOW=0.60, SIM_HIGH=0.75), clamped at the extremes.

Signal #2 — LLM-as-a-Judge. A structured prompt asks the judge for {alignment: 0–1, problem_type, reason}. On a live feature-creep test case, the judge scored alignment 0.20, problem_type "Feature Creep" with a correct one-line reason.

Combination. alignment = 0.4 × embedding_signal + 0.6 × judge_alignment (the judge understands intent; embeddings are cheap but noisy). Drift score = 1 − alignment, banded as:

Level Drift score System action
LOW < 0.30 continue
MEDIUM 0.30–0.55 soft correction (re-inject goal)
HIGH 0.55–0.75 strong repair (force focus back)
CRITICAL ≥ 0.75 strong repair now (rollback: roadmap)
Degraded mode: if every judge provider is unavailable, the detector still emits a report from embeddings alone — a busy API never blocks the loop.

4.4 Repair Module
Maps drift level → intervention. Soft correction re-injects the verbatim ledger text (never an LLM paraphrase) plus the judge's reason. Strong correction adds a STOP directive and writes a high-importance correction memory (survives compaction). A cooldown (hysteresis) prevents spamming a drifting agent with corrections every check. Every decision is logged to interventions.jsonl for evaluation.

4.5 Compaction Engine — safe forgetting
Triggered above 30 memory items. Protection rules (pure, unit-tested functions):

the Goal Ledger is a separate protected store — physically unreachable from compaction
items with importance ≥ 0.9 and all correction items survive verbatim
the 5 most recent items always survive (working context)
Everything older is replaced by one structured summary (progress, key decisions, open tasks) generated by the LLM — with a naive extractive fallback if providers are down. Raw items are archived to archive.jsonl (never deleted, still searchable).

Live demo result: 44 items → 8 items (37 archived), summary generated by LLM, ledger untouched.

5. Resilience engineering
   Real-world API reliability is part of the design:

Multi-provider failover — the judge layer tries Gemini first, then NVIDIA NIM models, transparently. Built after live 503/410/429 storms on both providers during development.
Tolerant JSON parsing — survives markdown fences and stray prose in model replies.
Graceful degradation everywhere — judge down → embedding-only verdicts; LLM down → extractive compaction summary; the loop never hard-crashes.
Full observability — every drift check (drift_log.jsonl) and intervention (interventions.jsonl) is persisted for evaluation and visualization. 6. Results
Verified during development (live runs):

Check Outcome
ON-TRACK state drift 0.00 → LOW → no intervention
VAGUE state (over-engineering) drift 0.70–0.76 → HIGH/CRITICAL → correction fired
DRIFTING state (feature creep) drift 0.77 → CRITICAL → strong correction; judge flagged "explicitly prohibited features"
Goal overwrite attempt correctly blocked (write-once lock)
Restart persistence goal + memory restored from disk
Compaction 44 → 8 items, corrections intact, ledger byte-identical
Agent-in-the-loop benchmark (baseline vs. protected agent, N trials with injected distractions: goal-completion rate, feature-creep rate, interventions, token overhead): in progress — results will be published here.

7. Quickstart
   git clone https://github.com/AtharvaAher26/Long-Horizon.gitcd Long-Horizonpython -m venv venvvenv\Scripts\activate # Windows (Linux/Mac: source venv/bin/activate)pip install -r requirements.txt
   Create .env (free tiers suffice):

GEMINI_API_KEY=... # embeddings (gemini-embedding-001) + primary judgeNVIDIA_API_KEY=... # fallback judge (build.nvidia.com)
Run the test suite (no network needed for unit tests):

pytest -v # 37 tests
Run the component demos in order:

python demo_phase1.py # Goal Ledger + Memory Store (run twice to see the lock)python demo_phase2.py # Drift Detector live verdictspython demo_phase3.py # Detect → decide → repair (end-to-end reflex arc)python demo_phase4.py # Safe compaction 8. Testing
37 tests across four suites, following a pure-core / effectful-shell split: all scoring math (calibration mapping, signal combination, level bands, compaction selection) is pure and tested offline in milliseconds; persistence and protection rules are tested against temporary files; LLM-dependent paths are exercised in the demos.

9. Tech stack
   Python 3.11+ · Pydantic v2 (data models) · OpenAI-compatible SDK (Gemini + NVIDIA NIM) · gemini-embedding-001 embeddings · pytest · Rich (console UX) · JSON/JSONL persistence

10. Roadmap
    Goal Ledger (write-once, protected)
    Memory Store (typed, persistent)
    Drift Detector (2 signals, calibrated, degraded mode)
    Repair Module (soft/strong, cooldown, logging)
    Compaction Engine (protection rules, archive, LLM + fallback)
    Demo agent + integrity loop (agent runs inside the layer, live)
    Benchmark: baseline vs. protected agent, N trials
    Drift-score-over-time visualization
    Rollback to checkpoints (reasoning-only agents)
    Optional: trained drift classifier (logistic regression on detector features)
11. Design doc
    This implementation follows a full research & design document covering failure-mode taxonomy, prior systems analysis (MemGPT/Letta, Mem0, Zep), and component specifications. Key design sources: hierarchical memory (MemGPT-style) with a hardened protected core, weighted multi-signal drift scoring, and priority-based safe compaction.

Built as an ML-systems project: semantic similarity via sentence embeddings, LLM-as-a-judge scoring, threshold calibration on validation pairs, and an evaluation harness for detection precision/recall.
