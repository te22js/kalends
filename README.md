# Kalends

A research substrate for **persistent AI worlds** in which agents maintain
temporally correct, causally grounded, individually bounded memories and
beliefs over a changing shared reality — and **Kalends-MemoryBench**, a
benchmark that scores memory architectures against an *exactly computed*
per-agent epistemic ground truth (no LLM judges, no annotation, fully
deterministic and replayable).

The core separation, enforced structurally:

```
WorldEvent → World State → Observation → Agent Belief/Memory → Decision → Action → New WorldEvent
```

- **Objective reality** is a deterministic fold over an append-only event
  ledger. No LLM can assert what happened.
- **Observation** is computed by the world (event scope + positions).
- **Belief** is per-agent with machine-checkable **provenance**:
  `heard it from Livia at E135 → Livia observed E84 directly` — including
  root signatures that distinguish independent evidence from shared ancestry.
- **Counterfactual surgery**: rerun the same world minus one event; because
  all randomness is context-keyed, the runs differ only through genuine
  causal channels.
- **Memory systems** receive only the information that actually reached each
  agent and are scored on belief accuracy, staleness (a stale belief can be
  the *correct* answer), supersession, source attribution, provenance,
  independent corroboration, and knowledge boundaries.

## Quickstart

No runtime dependencies. Python ≥ 3.10 (matplotlib only for plots).

```bash
python3 -m kalends simulate rumor --seed 42          # deterministic demo world
python3 -m kalends benchmark --seed 42               # 9 systems on the demo world
python3 -m kalends explain --agent Holconius --prop bakery.condition
python3 -m kalends counterfactual --seed 42 --drop 2 # causal-descendant diff
python3 -m kalends experiment --suite core --seeds 30 --out results/core
python3 -m pytest tests/                             # 40 invariant/audit/fuzz tests
```

## Headline results (30 seeds × 9 scenario families; full stats in results/)

Mean overall accuracy (±sd across seeds; boundary-violation rate in brackets):

| system | core avg | notes |
|---|---|---|
| recency (floor) | ~0.67 | strong floor; must be beaten |
| bm25 | ~0.78 | beats hashed-BoW vector everywhere |
| vector (hashed BoW) | ~0.70 [0.20–0.51] | classic RAG failure profile |
| vector+metadata | ~0.82 [~0.01] | filtering kills boundary hallucination |
| text_structured (parser) | ~0.83 [0.10–0.41] | the ceiling made real; entity-resolution failures |
| structured (**ceiling**) | ~0.94 [0.00] | by-construction; only alias misses |
| hybrid (naive) | ~0.92 [0.28–0.59] | **loses to structured on 9/9 families; collapses at scale (0.68 @ 128 agents)** |
| **hybrid_guarded** | **~0.96 [0.00–0.03]** | fallback only where the belief table has no opinion; beats both parents on 9/9 families, scale-stable (0.92 @ 128) |

The benchmark falsified the naive hybrid hypothesis, the failure analysis
located the mechanism (boundary hallucination through the fallback path), and
the guarded router — a one-rule change — wins everywhere. That loop
(benchmark → diagnosis → fix → verification) is the research story.
Details: [FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md),
[METHODOLOGY_AUDIT.md](METHODOLOGY_AUDIT.md) (which scores are meaningful vs
ceilings), plots in `results/plots/`.

## Repository map

| File | What it is |
|---|---|
| `ARCHITECTURE.md` | the system in ~10 minutes |
| `FORMALISM.md` | precise task definition (information sets, normative belief, root signatures) |
| `METHODOLOGY_AUDIT.md` | circularity/fairness audit; which numbers to trust |
| `RESEARCH_NOTES.md` | two literature passes incl. honest MemArena repositioning |
| `FAILURE_ANALYSIS.md` | categorized failure modes + the guarded-router case study |
| `TEMPORAL_RESOLUTION.md` | why adaptive resolution is future work |
| `DECISIONS.md` / `WHAT_I_BUILT.md` / `WORK_QUEUE.md` / `PAPER_OUTLINE.md` | project memory |
| `kalends/` | substrate: events, world, observation, epistemic oracle, rng, counterfactual, memory/, bench/, scenarios/ |
| `scripts/` | scaling, capacity, ablation, failure-analysis, plotting |
| `tests/` | 40 tests: invariants, oracle audit, property fuzzing |
| `results/` | 30-seed suites, scaling, capacity, ablations, failures, plots |

Baseline tag: `kalends-memorybench-v0` (the original single-scenario v0,
exactly reproducible).
