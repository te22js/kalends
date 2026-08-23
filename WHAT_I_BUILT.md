# WHAT_I_BUILT

Two sessions. Session 1 (2026-08-24) built v0 from an empty repo. Session 2
(same day, "do not stop at v0") turned it into experimental research
infrastructure. This file reflects the state after session 2.

## Executive summary

Kalends is now a deterministic, LLM-free epistemic simulator plus a
multi-family, multi-seed benchmark (Kalends-MemoryBench) that evaluates nine
memory architectures against exactly computed per-agent ground truth. The
headline finding is a complete falsify→diagnose→fix→verify loop: the naive
structured+vector hybrid — the architecture we originally expected to win —
**loses to structured-only on all 9 scenario families and collapses at scale**,
because its retrieval fallback hallucinates precisely on questions whose
correct answer is "I don't know." A one-rule *guarded* router derived from the
failure analysis beats both parents on all 9 families (d_z 1.2–2.5) with
near-zero knowledge-boundary violations and survives 128-agent worlds. The
methodology was audited for circularity before trusting any number, and the
literature pass found (and honestly repositioned against) MemArena, the
closest prior work.

## What changed since v0

- **Context-keyed randomness** (rng.py): every draw is a pure hash of
  (seed, context) → counterfactual runs differ only through causal channels.
- **Typed, serializable world configs + generator** (scenarios/generator.py):
  9 scenario families (propagation, supersession, private, overload, multihop,
  conflict + 3 held-out), adjective+noun entities that create natural hard
  negatives.
- **9 memory systems** (was 3): recency floor, BM25, vector, vector+recency,
  vector+metadata, text_structured (parser under test), structured (labeled
  ceiling), naive hybrid, guarded hybrid.
- **Richer oracle + questions**: independent-source vs shared-ancestry
  accounting (provenance root signatures), contradiction tags, paraphrase
  template families, claimed-origin content carried in tells (text *and*
  fields — equal information audited).
- **Experiment infrastructure**: multi-seed runner with mean/sd/median/95% CI
  and paired Cohen's d_z; scaling (8→128 agents); capacity pressure
  (25→unlimited, fifo vs importance); component ablations; automatic failure
  categorization; plots.
- **Counterfactual analysis** (counterfactual.py + CLI): exact causal
  descendants of a deleted event.
- **Test suite 17 → 40**: property fuzzing over random worlds, adversarial
  oracle audit, counterfactual purity checks.
- **New documents**: METHODOLOGY_AUDIT, FORMALISM, FAILURE_ANALYSIS,
  PAPER_OUTLINE, WORK_QUEUE; RESEARCH_NOTES second pass.

## Experiments actually run (exact configurations in results/*/configs.json)

| experiment | scope | where |
|---|---|---|
| core suite | 6 families × 30 seeds × 9 systems (~400–700 questions/world) | results/core |
| held-out suite | 3 untouched-parameter families × 30 seeds × 9 systems | results/heldout |
| scaling | 8/16/32/64/128 agents × 3 seeds × 7 systems | results/scaling |
| capacity | caps 25/50/100/200/∞ × {fifo, importance} × 4 systems × 8 seeds | results/capacity |
| ablations | 6 hybrid variants × 3 families × 10 seeds | results/ablations |
| failure taxonomy | 8 systems × 3 families × 10 seeds | results/failures |

## Main results (mean over 30 seeds; ±sd; paired CIs in results/*/summary.json)

- Trivial recency floor: 0.63–0.69 by family. BM25 0.71–0.80 — consistently
  above hashed-BoW vector (0.65–0.72, boundary violations 0.20–0.51).
- vector+metadata: 0.81–0.85 with violations ≈ 0.01–0.08 — metadata filtering
  alone removes nearly all boundary hallucination (57 → 1.5 per 1000).
- structured (ceiling): 0.93–0.95, zero violations, fails only aliases.
- text_structured: 0.81–0.85 — the measured "by-construction gap" vs
  structured is +0.09..+0.13 (d_z 1.9–3.5); it degrades at scale
  (0.86 → 0.61) from entity-resolution collisions.
- naive hybrid: 0.90–0.93, violations 0.28–0.59, **below structured on 9/9**,
  scale collapse 0.96 → 0.68 (8 → 128 agents).
- guarded hybrid: 0.95–0.97, violations 0.00–0.03, above structured on 9/9
  (+0.02..+0.03, d_z 1.4–2.0), 0.92 at 128 agents.
- Ablations (mean over 3 families): removing supersession −0.24 overall
  (contradiction 1.00→0.17); removing trust −0.23 (source 1.00→0.26);
  removing provenance −0.11; removing the naive fallback **+0.02**.
- Capacity: FIFO at cap 25 is catastrophic (structured 0.95→0.34); simple
  importance retention holds 0.945 at the same cap.

## Results that surprised me

1. Removing a component (the naive vector fallback) *improved* the system —
   the ablation table has a negative-cost component.
2. vector+metadata **improves** with scale (0.80→0.86) while everything
   text-routed degrades — filtering gains value as distractors multiply.
3. Importance-based eviction *raises* retrieval systems' boundary violations
   (~0.70) while raising accuracy: dropping filler removes safe noise, so
   wrong-but-confident propositional hits surface more often.
4. BM25 — no embeddings at all — beats the vector baseline everywhere.

## Results that weaken our thesis (mandatory section)

- **The original hybrid hypothesis is falsified as stated.** "Structured +
  vector fallback keeps both strengths" is wrong in this benchmark; the naive
  combination is worse than its symbolic half alone, everywhere, and
  degrades catastrophically with scale.
- **The guarded hybrid's margin over plain structured is small** (+0.02–0.03).
  It comes entirely from alias questions. A skeptic can say: "your best
  system is a dictionary with a fuzzy-matching side door."
- **structured's dominance is partly by construction** (it ingests
  oracle-format fields). The honest system (text_structured) is only ~0.83
  and scales poorly — symbolic memory's real-world value depends on parsing
  quality that we did not solve.
- **The vector column is hashed BoW, not real embeddings.** BM25 > vector
  suggests our vector baseline underestimates similarity retrieval; results
  labeled "vector" must not be read as "RAG with modern embeddings."
- **MemArena exists** (arXiv 2608.02613): visibility-matrix asymmetry with
  simulation-derived ground truth at larger scale. Our novelty is narrower
  than session 1 claimed — exactness, ancestry accounting, horizon-relative
  staleness, counterfactual surgery — not "first simulated-world memory
  benchmark."

## Methodological problems still unresolved

Ranked (from METHODOLOGY_AUDIT.md §8): (1) the trust/acceptance rule is
shared with systems via the `accepted` flag — trust *inference* is untested;
(2) closed vocabulary + exact match; (3) question grammar kinship with
renderings (paraphrase families mitigate, don't eliminate); (4) oracle
freshness semantics is one fixed revision rule; (5) no uncertainty/calibration
dimension yet.

## Major bugs discovered and fixed

- Alias questions inherited stale/supersession tags → polluted those
  dimensions (fixed session 1; DECISIONS #8).
- text_structured parsed 0.00 on the rumor world: ornate statement subjects
  ("fountain in the forum") never matched query subjects → token-overlap
  resolver.
- Vector similarity threshold mis-calibrated after renderings grew origin
  clauses (0.25 → 0.15, documented as fair tuning).
- A double-backgrounded shell killed one experiment batch silently — reran;
  lesson: check for the output files, not the launch.

## Architecture changes

Sequential RNG → context-keyed hash draws (enables counterfactuals; changed
ledger hashes; v0 preserved under tag `kalends-memorybench-v0`). Experiences
now carry claimed-origin fields and their text equivalents. StructuredMemory
gained ablation switches; hybrid gained the guarded router variant. Sparse
embeddings for scale.

## 15-minute repo walkthrough

1. `README.md` — headline results table (2 min).
2. `FORMALISM.md` — the task, precisely (3 min).
3. `METHODOLOGY_AUDIT.md` §7 — which numbers mean what (2 min).
4. `FAILURE_ANALYSIS.md` — the falsify→fix story (3 min).
5. Run: `python3 -m kalends benchmark --seed 42`,
   `python3 -m kalends explain --agent Holconius --prop bakery.condition`,
   `python3 -m kalends counterfactual --seed 42 --drop 2` (2 min).
6. Code, if desired: `kalends/epistemic.py` (the oracle),
   `kalends/memory/hybrid.py` (the guarded router),
   `kalends/bench/experiment.py` (the runner) (3 min).

## Research interpretation

What we can reasonably claim now:
- In deterministic worlds with exact epistemic ground truth, similarity
  retrieval without a time/schema model fails in characteristic, *measurable*
  ways (boundary hallucination, stale retrieval, distrust confusion), and
  those failures propagate into any hybrid that routes to it naively.
- Router policy — not retrieval quality — was the binding constraint on
  hybrid memory here; an epistemically honest router ("an empty belief table
  is an answer") is a cheap, verified fix.
- Supersession machinery is the single most load-bearing memory component in
  changing worlds; trust-filtering second.
- Retention policy under capacity pressure changes not just accuracy but the
  *type* of errors.

## What we absolutely cannot claim

- That any of this transfers to LLM-based memory/agents (untested).
- That vector retrieval per se is weak (hashed BoW only).
- First-ness of simulated-world memory evaluation (MemArena).
- Anything about human memory or cognition.
- That guarded hybrid is optimal — only that it beats the tested aiblings.

## Top 10 next actions (ranked by expected information gain)

1. **Real-embedding VectorMemory** (adapter exists at `vector.embed`): does
   the failure profile survive modern embeddings? Highest risk to our story.
2. **Full text-only track** for every system (strip fields; all systems
   parse): removes the last by-construction asymmetry and re-tests the
   ranking. (DECISIONS #15)
3. **LLM-answerer track** over each substrate with graded scoring — does the
   substrate ranking change when an LLM reads the memories?
4. **Counterfactual question family** (infrastructure done): "would agent X
   still believe P if event E hadn't happened?" — the benchmark dimension no
   transcript benchmark can pose.
5. **Revision-rule axis**: same worlds, several acceptance rules, measure
   ranking stability (answers methodological objection #1/#4).
6. **MemArena cross-evaluation**: run their backend styles on Kalends
   families; direct comparison for the paper's related-work section.
7. **Trust-inference track**: withhold the `accepted` flag, add scenario
   structure that makes reliability learnable, evaluate inference.
8. **Scale 256–1024 agents** + profile structured-store latency (currently
   benign: 0.3s at 128 agents).
9. **Claimed-vs-actual provenance questions** (distortion data already
   records both): can systems flag where distortion entered a chain?
10. **Uncertainty/calibration dimension** (confidence outputs exist but are
    unscored; needs a proper scoring rule).
