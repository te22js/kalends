# WHAT_I_BUILT

Session of 2026-08-24. The repository was empty at start; everything below is new.

## What happened, in order

1. **Audit:** nothing existed. Skipped to research.
2. **Research (RESEARCH_NOTES.md):** surveyed generative agents, event
   sourcing, epistemic logic, rumor models, and the 2024–26 wave of LLM-memory
   benchmarks (STALE, Supersede, LongMemEval, Belief Engine…). Conclusion: the
   defensible gap is a benchmark whose per-agent ground truth is *computed from
   a simulated world* rather than annotated — including staleness, provenance
   chains, and knowledge boundaries.
3. **Temporal resolution (TEMPORAL_RESOLUTION.md):** researched separately as
   asked. Verdict: mostly rediscovers discrete-event simulation + LLM compute
   scheduling; keep it out of paper one; the architecture stays compatible
   (sparse event ledger) at zero extra cost.
4. **Architecture (ARCHITECTURE.md):** froze the minimal design.
5. **Substrate (kalends/):** built and tested the whole pipeline — ledger,
   deterministic projection, observation rules, per-agent epistemic oracle with
   provenance chains, trust-gated belief revision, gossip with seeded
   distortion, trace export, CLI.
6. **Scenario (scenarios/rumor.py):** 14 named Pompeiians, 6 locations, 48
   hourly ticks. A bakery fire with few witnesses, a private theft, a late
   repair that only partially propagates, one habitual exaggerator (Rufus), a
   decoy proposition nobody can know, and a very late private event.
7. **Kalends-MemoryBench v0 (bench/):** ~380 oracle-generated questions per
   run across 9 tagged dimensions; harness replays each agent's experience
   stream into vector / structured / hybrid memories and scores exactly.
8. **Results:** in README.md and `results/`. Notable: hybrid does **not**
   strictly win (30% boundary-violation rate inherited from its vector
   fallback) — the experiment can falsify the hybrid hypothesis, as required.
9. **Tests:** 17 passing (`python3 -m pytest tests/`), covering determinism,
   replay-projection equivalence, knowledge boundaries, private-event
   containment, tell-has-source, belief/truth separation, stale-belief
   existence, propagation, distrust, and supersession ordering.

One mid-session fix worth knowing about: the first benchmark run had alias
questions inheriting the staleness tag, which made structured memory look bad
at staleness when it was actually failing alias retrieval. Dimension tags are
now single-purpose (DECISIONS.md #8) — a small example of why the oracle +
tagged-dimension design matters.

## 5-minute explanation

There is a tiny deterministic Pompeii. Everything that happens is an event in
an append-only ledger; world state is always recomputed from it. Each of 14
agents perceives only what it was present for, and the simulator keeps an exact
per-agent record of every piece of information that ever reached them and what
they should therefore believe — including who told them, who told *that*
person, whether the value was distorted en route, and whether newer information
superseded it. Three memory architectures are fed exactly those information
streams and then interrogated: What do you believe? Since when? Who's your
source? Did you see it yourself? Questions where the right answer is "unknown"
or a stale belief are the sharpest probes. Because ground truth is computed,
scoring is exact — no LLM judges, no annotation. Run it:
`python3 -m kalends simulate rumor --seed 42`, `python3 -m kalends benchmark`,
and `python3 -m kalends explain --agent Holconius --prop bakery.condition` to
see a real provenance chain for a stale belief.

## 30-minute walkthrough (reading order)

1. `ARCHITECTURE.md` — the map.
2. `kalends/events.py` then `kalends/world.py` — canonical reality (~120 lines).
3. `kalends/propositions.py` — beliefs' units and provenance chains.
4. `kalends/epistemic.py` — the oracle; the acceptance rule is the heart.
5. `kalends/simulation.py` — the loop (movement → incidents → gossip).
6. `kalends/scenarios/rumor.py` — the scenario, with its timeline docstring.
7. `kalends/memory/base.py`, then `vector.py`, `structured.py`, `hybrid.py`.
8. `kalends/bench/questions.py` and `harness.py` — how questions and scores
   are produced.
9. `tests/test_invariants.py` — the guarantees, executable.
10. `DECISIONS.md` — why everything above is the way it is.

## Open research questions (for you, not for delegation)

1. **Is the acceptance rule the right normative target?** Scoring against
   "trust ≥ θ and strictly fresher" is clean, but a reviewer may ask why that
   norm and not another. Consider making the revision rule an experimental
   axis (same memories, different norms) — that may itself be a contribution.
2. **What's the claim about vector memory?** v0's hashed-BoW retrieval shows
   architectural failure modes, but a skeptic will say "real embeddings fix
   the alias gap and maybe more." Decide whether paper-grade results require an
   embedding-model extra (DECISIONS.md #6).
3. **When does StructuredMemory stop being a ceiling?** The moment ingest gets
   raw text instead of parsed fields, it becomes a real system under test.
   That transition point is where the benchmark gets scientifically sharp.
4. **Scale laws:** do the gaps widen or close with 32 agents, 500 ticks, 50
   propositions? The generator makes this cheap to test; the answer determines
   whether the paper needs scale.
5. **What does the player-facing demo prove?** The "inspect the causal chain
   of a reaction" moment (product principle §6) already exists as
   `kalends explain` — think about what minimal interactivity would make the
   research visible without building a game.

## Next 5 highest-value actions (ranked)

1. **Multi-seed evaluation:** run N seeds, report mean ± spread per dimension
   (the harness is deterministic per seed; a `--seeds 1..20` flag is ~20 lines).
   Turns tables into defensible numbers.
2. **Scenario generator:** parameterize agent count, tick count, event density,
   distortion and trust rates → scaling curves and robustness (question 4).
3. **Text-ingest variant of StructuredMemory** (question 3) — a naive parser
   under test alongside the ceiling version.
4. **Claimed-vs-actual provenance questions:** the data already contains
   distorted tells whose claimed chains root in true observations; add
   questions probing whether systems can flag secondhand-of-secondhand and
   distortion exposure.
5. **Optional embedding-model extra for VectorMemory** behind
   `pip install kalends[embeddings]`, to check the failure profile survives
   real semantics (question 2).
