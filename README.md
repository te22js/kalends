# Kalends

A research substrate for **persistent AI worlds** in which agents maintain
temporally correct, causally grounded, individually bounded memories and
beliefs over a changing shared reality. First world: a deliberately tiny
Pompeii, 79 CE district. First artifact: **Kalends-MemoryBench**, a benchmark
that scores memory architectures against a *computed* per-agent epistemic
ground truth.

The core separation, enforced structurally:

```
WorldEvent → World State → Observation → Agent Belief/Memory → Decision → Action → New WorldEvent
```

- **Objective reality** is a deterministic fold over an append-only event
  ledger. No LLM anywhere can assert what happened.
- **Observation** is computed by the world (scope + positions), never claimed
  by agents.
- **Belief** is per-agent, with machine-checkable **provenance**:
  `heard it from Livia at E135 → Livia observed E84 directly`.
- **Memory systems** (vector / structured / hybrid) receive only the
  information that actually reached an agent, and are scored against the
  epistemic oracle — including on questions whose correct answer is a *stale*
  or *false* belief, and questions whose correct answer is "unknown".

## Quickstart

No dependencies. Python ≥ 3.10.

```bash
python3 -m kalends simulate rumor --seed 42
python3 -m kalends benchmark --seed 42
python3 -m kalends explain --agent Holconius --prop bakery.condition
python3 -m pytest tests/          # invariant + memory tests
```

(Optional: `pip install -e .` gives you a `kalends` command.)

## Current benchmark results (seed 42, rumor scenario, 382 questions)

| dimension | vector | structured | hybrid |
|---|---|---|---|
| alias retrieval (42) | 0.88 | 0.33 | 0.88 |
| belief accuracy (120) | 0.87 | 1.00 | 0.95 |
| knowledge boundary (40) | 0.70 | 1.00 | 0.70 |
| provenance class (50) | 0.90 | 1.00 | 1.00 |
| source attribution (50) | 0.30 | 1.00 | 1.00 |
| staleness handling (10) | 0.90 | 1.00 | 1.00 |
| supersession (74) | 0.61 | 1.00 | 1.00 |
| temporal (50) | 0.28 | 1.00 | 1.00 |
| **overall** | 0.67 | 0.93 | 0.96 |
| **boundary violation rate** | 0.30 | 0.00 | 0.30 |

Honest readings (see DECISIONS.md #7): structured memory's 1.00s are a
**by-construction ceiling** (it stores what the oracle stores); its real,
measured weakness is schema brittleness (alias 0.33). Vector memory shows the
classic RAG failure profile: no time model, weak source attribution, and it
*hallucinates across knowledge boundaries* 30% of the time (e.g. answering a
question about the temple treasury from a similar-sounding memory about
Gaius' silver). **Hybrid does not strictly dominate**: its vector fallback
inherits the boundary violations exactly where the structured path misses.

## Repository map

| File | What it is |
|---|---|
| `ARCHITECTURE.md` | the whole system in ~10 minutes |
| `RESEARCH_NOTES.md` | related work, what's ours vs. established |
| `TEMPORAL_RESOLUTION.md` | assessment of the adaptive-resolution idea |
| `DECISIONS.md` | every non-obvious choice, with reasons |
| `WHAT_I_BUILT.md` | plain-language session log + reading order |
| `kalends/` | the substrate (events, world, observation, epistemic oracle, memory, bench) |
| `kalends/scenarios/rumor.py` | the Pompeii rumor scenario |
| `tests/` | invariant tests (determinism, knowledge boundaries, belief/truth separation) |
| `results/` | canonical seed-42 trace + benchmark JSON |
